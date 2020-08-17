# -*- coding: utf-8 -*-
import locale
import logging
import sys
import time
import traceback
from subprocess import Popen, PIPE, STDOUT
from threading import Lock

import psutil as psutil

from utils import config, constant, logger, tool
from utils.exception import *
from utils.command_manager import CommandManager
from utils.parser_manager import ParserManager
from utils.permission_manager import PermissionManager
from utils.plugin_manager import PluginManager
from utils.rcon_manager import RconManager
from utils.language_manager import LanguageManager
from utils.reactor_manager import ReactorManager
from utils.server_status import ServerStatus
from utils.server_interface import ServerInterface
from utils.update_helper import UpdateHelper


class Server:
	def __init__(self, old_process=None):
		self.console_input_thread = None
		self.info_reactor_thread = None
		self.process = old_process  # type: Popen # the process for the server
		self.server_status = ServerStatus.STOPPED
		self.flag_interrupt = False  # ctrl-c flag
		self.flag_server_startup = False  # set to True after server startup
		self.flag_server_rcon_ready = False  # set to True after server started its rcon. used to start the rcon server
		self.flag_mcdr_exit = False  # MCDR exit flag
		self.flag_exit_naturally = True  # if MCDR exit after server stop. can be modified by plugins
		self.starting_server_lock = Lock()  # to prevent multiple start_server() call
		self.stop_lock = Lock()  # to prevent multiple stop() call

		# will be assigned in reload_config()
		self.encoding_method = None
		self.decoding_method = None

		self.logger = logger.Logger(self, constant.NAME_SHORT)
		self.logger.set_file(constant.LOGGING_FILE)
		self.server_logger = logger.ServerLogger('Server')
		self.language_manager = LanguageManager(self, constant.LANGUAGE_FOLDER)
		self.config = config.Config(self, constant.CONFIG_FILE)
		self.rcon_manager = RconManager(self)
		self.parser_manager = ParserManager(self, constant.PARSER_FOLDER)
		self.load_config()  # loads config, language, parsers

		self.reactor_manager = ReactorManager(self)
		self.server_interface = ServerInterface(self)
		self.command_manager = CommandManager(self)
		self.plugin_manager = PluginManager(self, constant.PLUGIN_FOLDER)
		self.load_plugins()
		self.permission_manager = PermissionManager(self, constant.PERMISSION_FILE)
		self.update_helper = UpdateHelper(self)
		self.update_helper.check_update_start()

	def __del__(self):
		try:
			if self.process and self.process.poll() is None:
				self.kill_server()
		except:
			pass

	# Translate info strings

	def translate(self, text, *args):
		result = self.language_manager.translate(text).strip()
		if len(args) > 0:
			result = result.format(*args)
		return result

	def t(self, text, *args):
		return self.translate(text, *args)

	# Loaders

	def load_config(self):
		self.config.read_config()

		self.language_manager.load_languages()
		self.language_manager.set_language(self.config['language'])
		self.logger.info(self.t('server.load_config.language_set', self.config['language']))

		self.logger.set_level(logging.DEBUG if self.config['debug_mode'] else logging.INFO)
		if self.config['debug_mode']:
			self.logger.info(self.t('server.load_config.debug_mode_on'))

		self.parser_manager.install_parser(self.config['parser'])
		self.logger.info(self.t('server.load_config.parser_set', self.config['parser']))

		self.encoding_method = self.config['encoding'] if self.config['encoding'] is not None else sys.getdefaultencoding()
		self.decoding_method = self.config['decoding'] if self.config['decoding'] is not None else locale.getpreferredencoding()
		self.logger.info(self.t('server.load_config.encoding_decoding_set', self.encoding_method, self.decoding_method))

		self.connect_rcon()

	def load_plugins(self):
		self.logger.info(self.plugin_manager.refresh_all_plugins())

	# MCDR status

	def is_server_running(self):
		return self.process is not None

	def is_server_startup(self):
		return self.flag_server_startup

	def is_server_rcon_ready(self):
		return self.flag_server_rcon_ready

	def is_interrupt(self):
		return self.flag_interrupt

	def is_mcdr_exit(self):
		return self.flag_mcdr_exit

	def is_exit_naturally(self):
		return self.flag_exit_naturally

	def set_exit_naturally(self, flag):
		self.flag_exit_naturally = flag
		self.logger.debug('flag_exit_naturally has set to "{}"'.format(self.flag_exit_naturally))

	def set_server_status(self, status):
		self.server_status = status
		self.logger.debug('Server status has set to "{}"'.format(ServerStatus.translate_key(status)))

	# MCDR server

	def start_server(self):
		"""
		try to start the server process
		return True if the server process has started successfully
		return False if the server is already running or start_server has been called by other

		:return: a bool as above
		:rtype: bool
		"""
		acquired = self.starting_server_lock.acquire(blocking=False)
		if not acquired:
			return False
		try:
			if self.is_interrupt():
				self.logger.warning(self.t('server.start_server.already_interrupted'))
				return False
			if self.is_server_running():
				self.logger.warning(self.t('server.start_server.start_twice'))
				return False
			try:
				start_command = self.config['start_command']
				self.logger.info(self.t('server.start_server.starting', start_command))
				self.process = Popen(start_command, cwd=self.config['working_directory'], stdin=PIPE, stdout=PIPE, stderr=STDOUT, shell=True)
			except:
				self.logger.exception(self.t('server.start_server.start_fail'))
				return False
			else:
				self.set_server_status(ServerStatus.RUNNING)
				self.set_exit_naturally(True)
				self.logger.info(self.t('server.start_server.pid_info', self.process.pid))
				return True
		finally:
			self.starting_server_lock.release()

	def start(self):
		"""
		The entry method to start MCDR
		Try to start the server. if succeeded the console thread will start and MCDR will start ticking

		:raise: Raise ServerStartError if the server is already running or start_server has been called by other
		"""
		def start_thread(target, args, name):
			self.logger.debug('{} thread starting'.format(name))
			thread = tool.start_thread(target, args, name)
			return thread

		if not self.start_server():
			raise ServerStartError()
		if not self.config['disable_console_thread']:
			self.console_input_thread = start_thread(self.console_input, (), 'Console')
		else:
			self.logger.info('Console thread disabled')
		self.info_reactor_thread = start_thread(self.reactor_manager.run, (), 'InfoReactor')
		self.run()
		return self.process

	def kill_server(self):
		"""
		Kill the server process group
		"""
		if self.process and self.process.poll() is None:
			self.logger.info(self.t('server.kill_server.killing'))
			try:
				for child in psutil.Process(self.process.pid).children(recursive=True):
					child.kill()
					self.logger.info(self.t('server.kill_server.process_killed', child.pid))
			except psutil.NoSuchProcess:
				pass
			self.process.kill()
			self.logger.info(self.t('server.kill_server.process_killed', self.process.pid))
		else:
			raise IllegalCall("Server process has already been terminated")

	def interrupt(self):
		"""
		Interrupt MCDR
		The first call will softly stop the server and the later calls will kill the server
		Return if it's the first try
		:rtype: bool
		"""
		self.logger.debug('Interrupting, first strike = {}'.format(not self.is_interrupt()))
		self.stop(forced=self.is_interrupt())
		ret = self.is_interrupt()
		self.flag_interrupt = True
		return ret

	def stop(self, forced=False):
		"""
		stop the server

		:param forced: an optional bool. If it's False (default) MCDR will stop the server by sending the STOP_COMMAND from the
		current parser. If it's True MCDR will just kill the server process group
		"""
		with self.stop_lock:
			if not self.is_server_running():
				self.logger.warning(self.t('server.stop.stop_when_stopped'))
				return
			self.set_server_status(ServerStatus.STOPPING)
			if not forced:
				try:
					self.send(self.parser_manager.get_stop_command())
				except:
					self.logger.error(self.t('server.stop.stop_fail'))
					forced = True
			if forced:
				try:
					self.kill_server()
				except IllegalCall:
					pass

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
			self.logger.warning(self.t('server.send.send_when_stopped'))

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
						self.logger.info(self.t('server.receive.wait_stop'))
				raise ServerStopped()
			else:
				try:
					text = text.decode(self.decoding_method)
				except:
					self.logger.error(self.t('server.receive.decode_fail', text))
					raise
				return text.rstrip().lstrip()

	def on_server_stop(self):
		return_code = self.process.poll()
		self.logger.info(self.t('server.on_server_stop.show_stopcode', return_code))
		self.process = None
		self.flag_server_startup = False
		self.flag_server_rcon_ready = False
		self.set_server_status(ServerStatus.STOPPED)
		self.plugin_manager.call('on_server_stop', (self.server_interface, return_code), wait=True)

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
			text = self.parser_manager.get_parser().pre_parse_server_stdout(text)
		except:
			self.logger.warning(self.t('server.tick.pre_parse_fail'))
		self.server_logger.info(text)

		try:
			parsed_result = self.parser_manager.get_parser().parse_server_stdout(text)
		except:
			self.logger.debug('Fail to parse text "{}" from stdout of the server, using raw parser'.format(text))
			for line in traceback.format_exc().splitlines():
				self.logger.debug('    {}'.format(line))
			parsed_result = self.parser_manager.get_basic_parser().parse_server_stdout(text)
		else:
			self.logger.debug('Parsed text from server stdin:')
			for line in parsed_result.format_text().splitlines():
				self.logger.debug('    {}'.format(line))
		self.reactor_manager.put_info(parsed_result)

	def on_mcdr_stop(self):
		try:
			if self.is_interrupt():
				self.logger.info(self.t('server.on_mcdr_stop.user_interrupted'))
			else:
				self.logger.info(self.t('server.on_mcdr_stop.server_stop'))
			self.plugin_manager.call('on_mcdr_stop', (self.server_interface,), wait=True)
			self.logger.info(self.t('server.on_mcdr_stop.bye'))
		except KeyboardInterrupt:  # I don't know why there sometimes will be a KeyboardInterrupt if MCDR is stopped by ctrl-c
			pass
		except:
			self.logger.exception(self.t('server.on_mcdr_stop.stop_error'))
		finally:
			self.flag_mcdr_exit = True

	def should_keep_running(self):
		if self.is_interrupt():
			return False
		return self.server_status not in [ServerStatus.STOPPED] or not self.flag_exit_naturally

	def run(self):
		"""
		the main loop of MCDR
		:return: None
		"""
		while self.should_keep_running():
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
					self.logger.critical(self.t('server.run.error'), exc_info=True)
		self.on_mcdr_stop()

	def console_input(self):
		"""
		the thread for processing console input
		:return: None
		"""
		while True:
			try:
				text = input()
				try:
					parsed_result = self.parser_manager.get_parser().parse_console_command(text)
				except:
					self.logger.exception(self.t('server.console_input.parse_fail', text))
				else:
					self.logger.debug('Parsed text from console input:')
					for line in parsed_result.format_text().splitlines():
						self.logger.debug('    {}'.format(line))
					self.reactor_manager.put_info(parsed_result)
			except (KeyboardInterrupt, EOFError, SystemExit, IOError) as e:
				self.logger.debug('Exception {} {} caught in console_input()'.format(type(e), e))
				self.interrupt()
			except:
				self.logger.exception(self.t('server.console_input.error'))

	def connect_rcon(self):
		self.rcon_manager.disconnect()
		if self.config['enable_rcon'] and self.is_server_rcon_ready():
			self.rcon_manager.connect(self.config['rcon_address'], self.config['rcon_port'], self.config['rcon_password'])
