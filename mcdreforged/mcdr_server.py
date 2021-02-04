import locale
import os
import sys
import time
import traceback
from subprocess import Popen, PIPE, STDOUT
from threading import Lock
from typing import Optional

import psutil

from mcdreforged import constant
from mcdreforged.command.command_manager import CommandManager
from mcdreforged.config import Config
from mcdreforged.executor.console_handler import ConsoleHandler
from mcdreforged.executor.task_executor import TaskExecutor
from mcdreforged.executor.update_helper import UpdateHelper
from mcdreforged.executor.watchdog import WatchDog
from mcdreforged.handler.server_handler_manager import ServerHandlerManager
from mcdreforged.info import Info
from mcdreforged.info_reactor.info_reactor_manager import InfoReactorManager
from mcdreforged.language_manager import LanguageManager
from mcdreforged.mcdr_state import ServerState, MCDReforgedState, MCDReforgedFlag
from mcdreforged.minecraft.rcon.rcon_manager import RconManager
from mcdreforged.permission.permission_manager import PermissionManager
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.plugin.plugin_manager import PluginManager
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.utils import logger, file_util
from mcdreforged.utils.exception import IllegalCallError, ServerStopped, ServerStartError, IllegalStateError
from mcdreforged.utils.logger import DebugOption, MCDReforgedLogger


class MCDReforgedServer:
	process: Optional[Popen]

	def __init__(self):
		# TODO console args
		self.mcdr_state = MCDReforgedState.INITIALIZING
		self.server_state = ServerState.STOPPED
		self.process = None  # type: Optional[PIPE]
		self.flags = MCDReforgedFlag.NONE
		self.starting_server_lock = Lock()  # to prevent multiple start_server() call
		self.stop_lock = Lock()  # to prevent multiple stop() call

		# will be assigned in on_config_changed()
		self.encoding_method = None  # type: Optional[str]
		self.decoding_method = None  # type: Optional[str]

		# --- Constructing fields ---
		self.logger = MCDReforgedLogger(self)
		self.logger.set_file(constant.LOGGING_FILE)
		self.server_interface = ServerInterface(self)
		self.task_executor = TaskExecutor(self)
		self.console_handler = ConsoleHandler(self)
		self.watch_dog = WatchDog(self)
		self.update_helper = UpdateHelper(self)
		self.language_manager = LanguageManager(self.logger)
		self.config = Config(self.logger)
		self.rcon_manager = RconManager(self)
		self.server_handler_manager = ServerHandlerManager(self)
		self.reactor_manager = InfoReactorManager(self)
		self.command_manager = CommandManager(self)
		self.plugin_manager = PluginManager(self)
		self.permission_manager = PermissionManager(self)

		# --- Initialize fields instance ---
		file_missing = False
		try:
			self.load_config(allowed_missing_file=False)  # loads config, language, handlers
		except FileNotFoundError:
			self.logger.error('Config is missing, default config generated')
			self.config.save_default()
			file_missing = True
		try:
			self.permission_manager.load_permission_file(allowed_missing_file=False)
		except FileNotFoundError:
			self.logger.error('Permission file is missing, default permission file generated')
			self.permission_manager.save_default()
			file_missing = True
		if file_missing:
			self.on_first_start()
			return
		self.plugin_manager.register_permanent_plugins()

		self.set_mcdr_state(MCDReforgedState.INITIALIZED)

	def __del__(self):
		try:
			if self.process and self.process.poll() is None:
				self.kill_server()
		except:
			pass

	def on_first_start(self):
		self.logger.info('Some of the user files are missing, check them before launch MCDR again')
		default_config = self.config.get_default()
		file_util.touch_directory(default_config['working_directory'])
		self.plugin_manager.set_plugin_directories(default_config['plugin_directories'])  # to touch the directory

	# --------------------------
	#   Translate info strings
	# --------------------------

	def tr(self, text, *args, allow_failure=True):
		result = self.language_manager.translate(text, allow_failure).strip('\r\n')
		if len(args) > 0:
			result = result.format(*args)
		return result

	# --------------------------
	#          Loaders
	# --------------------------

	def load_config(self, *, allowed_missing_file=True):
		has_missing = self.config.read_config(allowed_missing_file)
		# load the language first to make sure tr() is available
		self.on_config_changed()
		if has_missing:
			for line in self.tr('config.missing_config').splitlines():
				self.logger.warning(line)

	def on_config_changed(self):
		logger.console_color_disabled = self.config['disable_console_color']
		self.logger.set_debug_options(self.config['debug'])
		if self.config.is_debug_on():
			self.logger.info(self.tr('mcdr_server.on_config_changed.debug_mode_on'))

		self.language_manager.set_language(self.config['language'])
		self.logger.info(self.tr('mcdr_server.on_config_changed.language_set', self.config['language']))

		self.encoding_method = self.config['encoding'] if self.config['encoding'] is not None else sys.getdefaultencoding()
		self.decoding_method = self.config['decoding'] if self.config['decoding'] is not None else locale.getpreferredencoding()
		self.logger.info(self.tr('mcdr_server.on_config_changed.encoding_decoding_set', self.encoding_method, self.decoding_method))

		self.plugin_manager.set_plugin_directories(self.config['plugin_directories'])
		self.logger.info(self.tr('mcdr_server.on_config_changed.plugin_directories_set', self.encoding_method, self.decoding_method))
		for directory in self.plugin_manager.plugin_directories:
			self.logger.info('- {}'.format(directory))

		self.reactor_manager.register_reactors(self.config['custom_info_reactors'])

		self.server_handler_manager.register_handlers(self.config['custom_handlers'])
		self.server_handler_manager.set_handler(self.config['handler'])
		self.logger.info(self.tr('mcdr_server.on_config_changed.handler_set', self.config['handler']))

		self.connect_rcon()

	def load_plugins(self):
		self.plugin_manager.refresh_all_plugins()
		self.logger.info(self.plugin_manager.last_operation_result.to_rtext(show_path=True))

	def on_plugin_changed(self):
		self.command_manager.clear_command()
		self.plugin_manager.registry_storage.export_commands(self.command_manager.register_command)

	# ---------------------------
	#   State Getters / Setters
	# ---------------------------

	def is_server_running(self):
		return self.server_state.in_state({ServerState.RUNNING, ServerState.STOPPING})

	# Flags

	def is_server_startup(self):
		return MCDReforgedFlag.SERVER_STARTUP in self.flags

	def is_server_rcon_ready(self):
		return MCDReforgedFlag.SERVER_RCON_READY in self.flags

	def is_interrupt(self):
		return MCDReforgedFlag.INTERRUPT in self.flags

	def is_mcdr_exit(self):
		return self.mcdr_in_state(MCDReforgedState.STOPPED)

	def is_mcdr_about_to_exit(self):
		return self.mcdr_in_state({MCDReforgedState.PRE_STOPPED, MCDReforgedState.STOPPED})

	def is_exit_naturally(self):
		return MCDReforgedFlag.EXIT_NATURALLY in self.flags

	def with_flag(self, flag: MCDReforgedFlag):
		self.flags |= flag

	def remove_flag(self, flag: MCDReforgedFlag):
		self.flags &= ~flag

	def set_exit_naturally(self, flag):
		if flag:
			self.with_flag(MCDReforgedFlag.EXIT_NATURALLY)
		else:
			self.remove_flag(MCDReforgedFlag.EXIT_NATURALLY)
		self.logger.debug('flag_exit_naturally has set to "{}"'.format(flag), option=DebugOption.MCDR)

	# State

	def server_in_state(self, states):
		return self.server_state.in_state(states)

	def mcdr_in_state(self, states):
		return self.mcdr_state.in_state(states)

	def is_initialized(self):
		return self.mcdr_in_state(MCDReforgedState.INITIALIZED)

	def set_server_state(self, state):
		self.server_state = state
		self.logger.debug('Server state has set to "{}"'.format(state), option=DebugOption.MCDR)

	def set_mcdr_state(self, state):
		self.mcdr_state = state
		self.logger.debug('MCDR state has set to "{}"'.format(state), option=DebugOption.MCDR)

	def should_keep_looping(self):
		"""
		A criterion for sub threads to determine if it should keep looping
		:rtype: bool
		"""
		if self.server_in_state(ServerState.STOPPED):
			if self.is_interrupt():  # if interrupted and stopped
				return False
			return not self.is_exit_naturally()  # if the sever exited naturally, exit MCDR
		return not self.is_mcdr_exit()

	# --------------------------
	#      Server Controls
	# --------------------------

	def start_server(self):
		"""
		try to start the server process
		return True if the server process has started successfully
		return False if the server is not able to start

		:return: a bool as above
		:rtype: bool
		"""
		with self.starting_server_lock:
			if self.is_interrupt():
				self.logger.warning(self.tr('mcdr_server.start_server.already_interrupted'))
				return False
			if self.is_server_running():
				self.logger.warning(self.tr('mcdr_server.start_server.start_twice'))
				return False
			if self.is_mcdr_about_to_exit():
				self.logger.warning(self.tr('mcdr_server.start_server.about_to_exit'))
				return False
			cwd = self.config['working_directory']
			if not os.path.isdir(cwd):
				self.logger.error(self.tr('mcdr_server.start_server.cwd_not_existed', cwd))
				return False
			try:
				start_command = self.config['start_command']
				self.logger.info(self.tr('mcdr_server.start_server.starting', start_command))
				self.process = Popen(start_command, cwd=self.config['working_directory'], stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
			except:
				self.logger.exception(self.tr('mcdr_server.start_server.start_fail'))
				return False
			else:
				self.on_server_start()
				return True

	def kill_server(self):
		"""
		Kill the server process group
		"""
		if self.process and self.process.poll() is None:
			self.logger.info(self.tr('mcdr_server.kill_server.killing'))
			try:
				for child in psutil.Process(self.process.pid).children(recursive=True):
					child.kill()
					self.logger.info(self.tr('mcdr_server.kill_server.process_killed', child.pid))
			except psutil.NoSuchProcess:
				pass
			self.process.kill()
			self.logger.info(self.tr('mcdr_server.kill_server.process_killed', self.process.pid))
		else:
			raise IllegalCallError("Server process has already been terminated")

	def interrupt(self):
		"""
		Interrupt MCDR
		The first call will softly stop the server and the later calls will kill the server
		Return if it's the first try
		:rtype: bool
		"""
		self.logger.info('Interrupting, first strike = {}'.format(not self.is_interrupt()))
		self.stop(forced=self.is_interrupt())
		ret = self.is_interrupt()
		self.with_flag(MCDReforgedFlag.INTERRUPT)
		return ret

	def stop(self, forced=False):
		"""
		Stop the server

		:param forced: an optional bool. If it's False (default) MCDR will stop the server by sending the STOP_COMMAND from the
		current handler. If it's True MCDR will just kill the server process group
		"""
		with self.stop_lock:
			if not self.is_server_running():
				self.logger.warning(self.tr('mcdr_server.stop.stop_when_stopped'))
				return
			self.set_server_state(ServerState.STOPPING)
			if not forced:
				try:
					self.send(self.server_handler_manager.get_current_handler().get_stop_command())
				except:
					self.logger.error(self.tr('mcdr_server.stop.stop_fail'))
					forced = True
			if forced:
				try:
					self.kill_server()
				except IllegalCallError:
					pass

	# --------------------------
	#      Server Logics
	# --------------------------

	def on_server_start(self):
		self.set_server_state(ServerState.RUNNING)
		self.set_exit_naturally(True)  # Set after server state is set to RUNNING, or MCDR might have a chance to exit if the server is started by other thread
		self.logger.info(self.tr('mcdr_server.start_server.pid_info', self.process.pid))
		self.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_START, ())

	def on_server_stop(self):
		return_code = self.process.poll()
		self.logger.info(self.tr('mcdr_server.on_server_stop.show_stopcode', return_code))
		self.process.stdin.close()
		self.process.stdout.close()
		self.process = None
		self.set_server_state(ServerState.STOPPED)
		self.remove_flag(MCDReforgedFlag.SERVER_STARTUP | MCDReforgedFlag.SERVER_RCON_READY)  # removes this two
		self.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_STOP, (return_code,), wait=True)

	def send(self, text, ending='\n', encoding=None):
		"""
		Send a text to server's stdin if the server is running

		:param text: A str or a bytes you want to send. if text is a str then it will attach the ending parameter to its
		back
		:param str ending: The suffix of a command with a default value \n
		:param str encoding: The encoding method for the text. If it's not given used the method in config
		"""
		if encoding is None:
			encoding = self.encoding_method
		if type(text) is str:
			text = (text + ending).encode(encoding)
		if self.is_server_running():
			self.process.stdin.write(text)
			self.process.stdin.flush()
		else:
			self.logger.warning(self.tr('mcdr_server.send.send_when_stopped'))

	def receive(self):
		"""
		Try to receive a str from server's stdout. This will block the current thread
		If server has stopped it will wait up to 10s for the server process to exit, then raise a ServerStopped exception

		:rtype: str
		:raise: ServerStopped
		"""
		while True:
			try:
				text = next(iter(self.process.stdout))
			except StopIteration:  # server process has stopped
				for i in range(constant.WAIT_TIME_AFTER_SERVER_STDOUT_END_SEC * 10):
					if self.process.poll() is not None:
						break
					time.sleep(0.1)
					if i % 10 == 0:
						self.logger.info(self.tr('mcdr_server.receive.wait_stop'))
				raise ServerStopped()
			else:
				try:
					text = text.decode(self.decoding_method)
				except:
					self.logger.error(self.tr('mcdr_server.receive.decode_fail', text))
					raise
				return text.rstrip('\n\r').lstrip('\n\r')

	def tick(self):
		"""
		ticking MCDR:
		try to receive a new line from server's stdout and parse / display / process the text
		"""
		try:
			text = self.receive()
		except ServerStopped:
			self.on_server_stop()
			return
		try:
			text = self.server_handler_manager.get_current_handler().pre_parse_server_stdout(text)
		except:
			self.logger.warning(self.tr('mcdr_server.tick.pre_parse_fail'))

		parsed_result: Info
		try:
			parsed_result = self.server_handler_manager.get_current_handler().parse_server_stdout(text)
		except:
			if self.logger.should_log_debug(option=DebugOption.HANDLER):  # traceback.format_exc() is costly
				self.logger.debug('Fail to parse text "{}" from stdout of the server, using raw handler'.format(text), no_check=True)
				for line in traceback.format_exc().splitlines():
					self.logger.debug('    {}'.format(line), no_check=True)
			parsed_result = self.server_handler_manager.get_basic_handler().parse_server_stdout(text)
		else:
			if self.logger.should_log_debug(option=DebugOption.HANDLER):
				self.logger.debug('Parsed text from server stdout:', no_check=True)
				for line in parsed_result.format_text().splitlines():
					self.logger.debug('    {}'.format(line), no_check=True)
		self.server_handler_manager.detect_text(text)
		self.reactor_manager.put_info(parsed_result)

	def on_mcdr_start(self):
		self.task_executor.start()
		self.task_executor.enqueue_regular_task(self.load_plugins)
		self.task_executor.wait_till_finish_all_task()
		self.plugin_manager.dispatch_event(MCDRPluginEvents.MCDR_START, ())
		if not self.config['disable_console_thread']:
			self.console_handler.start()
		else:
			self.logger.info(self.tr('mcdr_server.on_mcdr_start.console_disabled'))
		if not self.start_server():
			raise ServerStartError()
		self.update_helper.start()
		self.watch_dog.start()
		self.server_handler_manager.start_handler_detection()
		self.set_mcdr_state(MCDReforgedState.RUNNING)

	def on_mcdr_stop(self):
		try:
			self.set_mcdr_state(MCDReforgedState.PRE_STOPPED)
			if self.is_interrupt():
				self.logger.info(self.tr('mcdr_server.on_mcdr_stop.user_interrupted'))
			else:
				self.logger.info(self.tr('mcdr_server.on_mcdr_stop.server_stop'))

			self.watch_dog.stop()  # it's ok for plugins to take some time
			self.watch_dog.join()
			self.plugin_manager.dispatch_event(MCDRPluginEvents.MCDR_STOP, (), wait=True)

			self.logger.info(self.tr('mcdr_server.on_mcdr_stop.bye'))
		except KeyboardInterrupt:  # I don't know why there sometimes will be a KeyboardInterrupt if MCDR is stopped by ctrl-c
			pass
		except:
			self.logger.exception(self.tr('mcdr_server.on_mcdr_stop.stop_error'))
		finally:
			self.set_mcdr_state(MCDReforgedState.STOPPED)

	def start(self):
		"""
		The entry method to start MCDR
		Try to start the server. if succeeded the console thread will start and MCDR will start ticking

		:raise: IllegalStateError if MCDR is in wrong state
		:raise: ServerStartError if the server is already running or start_server has been called by other
		"""
		if not self.mcdr_in_state(MCDReforgedState.INITIALIZED):
			if self.mcdr_in_state(MCDReforgedState.INITIALIZING):
				raise IllegalStateError('This instance is not fully initialized')
			else:
				raise IllegalStateError('MCDR can only start once')
		self.main_loop()
		return self.process

	def main_loop(self):
		"""
		The main loop of MCDR
		"""
		self.on_mcdr_start()
		while self.should_keep_looping():
			try:
				if self.is_server_running():
					self.tick()
				else:
					time.sleep(0.01)
			except KeyboardInterrupt:
				self.interrupt()
			except:
				if self.is_interrupt():
					break
				else:
					self.logger.critical(self.tr('mcdr_server.run.error'), exc_info=True)
		self.on_mcdr_stop()

	def connect_rcon(self):
		self.rcon_manager.disconnect()
		if self.config['rcon']['enable'] and self.is_server_rcon_ready():
			self.rcon_manager.connect(self.config['rcon']['address'], self.config['rcon']['port'], self.config['rcon']['password'])
