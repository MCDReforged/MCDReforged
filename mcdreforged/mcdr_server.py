import concurrent.futures as cf
import dataclasses
import locale
import os
import threading
import time
import traceback
from importlib.metadata import PackageNotFoundError, Distribution
from pathlib import Path
from typing import Optional, Callable, Any, TYPE_CHECKING, List, Dict

from ruamel.yaml import YAMLError

from mcdreforged.command.command_manager import CommandManager
from mcdreforged.constants import core_constant
from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.executor.console_handler import ConsoleHandler
from mcdreforged.executor.task_executor_async import AsyncTaskExecutor
from mcdreforged.executor.task_executor_sync import SyncTaskExecutor
from mcdreforged.executor.telemetry_reporter import TelemetryReporterScheduler
from mcdreforged.executor.update_helper import UpdateHelper
from mcdreforged.executor.watchdog import WatchDog
from mcdreforged.handler.server_handler_manager import ServerHandlerManager
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.info_filter import InfoFilterHolder
from mcdreforged.info_reactor.info_reactor_manager import InfoReactorManager
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.formatter import MCColorFormatControl
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.mcdr_config import MCDReforgedConfigManager, MCDReforgedConfig
from mcdreforged.mcdr_server_args import MCDReforgedServerArgs
from mcdreforged.mcdr_state import ServerState, MCDReforgedState, MCDReforgedFlag
from mcdreforged.minecraft.rcon.rcon_manager import RconManager
from mcdreforged.permission.permission_manager import PermissionManager
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.plugin.plugin_manager import PluginManager
from mcdreforged.plugin.si.server_interface import ServerInterface
from mcdreforged.preference.preference_manager import PreferenceManager
from mcdreforged.process.server_process_manager import ServerProcessManager
from mcdreforged.translation.language_fallback_handler import LanguageFallbackHandler
from mcdreforged.translation.translation_manager import TranslationManager
from mcdreforged.translation.translator import Translator
from mcdreforged.utils import file_utils, request_utils, collection_utils, thread_utils, os_utils
from mcdreforged.utils.exception import ServerStartError, IllegalStateError
from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_registry import PluginRegistryStorage


class _ReceiveDecodeError(ValueError):
	pass


class _ServerProcessStopped(Exception):
	pass


@dataclasses.dataclass(frozen=True)
class _ParsedServerOutput:
	line: str
	is_stdout: bool


_ConfigLoadedCallback = Callable[[MCDReforgedConfig, bool], Any]
_UNSET: Any = object()


class MCDReforgedServer:
	def __init__(self, args: MCDReforgedServerArgs):
		self.mcdr_state: MCDReforgedState = MCDReforgedState.INITIALIZING
		self.server_state: ServerState = ServerState.STOPPED
		self.server_state_cv: threading.Condition = threading.Condition()
		self.server_information: ServerInformation = ServerInformation()
		self.__flags = MCDReforgedFlag.NONE
		self.__starting_server_lock = threading.Lock()  # to prevent multiple start_server() call
		self.__no_server_start = args.no_server_start
		self.__stop_lock = threading.Lock()  # to prevent multiple stop() call
		self.__config_change_lock = threading.Lock()
		self.__config_changed_callbacks: List[_ConfigLoadedCallback] = []

		# will be assigned in on_config_changed()
		self.__encoding_method: Optional[str] = None
		self.__decoding_method: List[str] = []

		# --- Constructing fields --- #
		self.logger: MCDReforgedLogger = MCDReforgedLogger()
		self.process_manager: ServerProcessManager = ServerProcessManager(self)
		self.config_manager: MCDReforgedConfigManager = MCDReforgedConfigManager(self.logger, args.config_file_path)
		self.permission_manager: PermissionManager = PermissionManager(self, args.permission_file_path)
		self.basic_server_interface: ServerInterface = ServerInterface(self)
		self.task_executor: SyncTaskExecutor = SyncTaskExecutor(self)
		self.async_task_executor: AsyncTaskExecutor = AsyncTaskExecutor(self)
		self.console_handler: ConsoleHandler = ConsoleHandler(self)
		self.watch_dog: WatchDog = WatchDog(self)
		self.update_helper: UpdateHelper = UpdateHelper(self)
		self.telemetry_reporter_scheduler: TelemetryReporterScheduler = TelemetryReporterScheduler(self)
		self.translation_manager: TranslationManager = TranslationManager(self.logger)
		self.rcon_manager: RconManager = RconManager(self)
		self.server_handler_manager: ServerHandlerManager = ServerHandlerManager(self)
		self.reactor_manager: InfoReactorManager = InfoReactorManager(self)
		self.command_manager: CommandManager = CommandManager(self)
		self.plugin_manager: PluginManager = PluginManager(self)
		self.preference_manager: PreferenceManager = PreferenceManager(self)
		self.__tr = self.create_internal_translator('mcdr_server')

		self.__check_environment()

		# --- Input arguments "generate_default_only" processing --- #
		if args.generate_default_only:
			self.config_manager.save_default()
			self.permission_manager.save_default()
			return

		# --- Initialize fields instance --- #
		self.translation_manager.load_translations()  # translations are used for logging, so load them first
		if args.initialize_environment or args.auto_init:
			# Prepare config / permission files if they're missing
			if not self.config_manager.file_presents():
				self.config_manager.save_default()
				file_utils.touch_directory(self.config.working_directory)  # create server/ folder
			if not self.permission_manager.file_presents():
				self.permission_manager.save_default()

		# Check if there's any file missing
		# If there's any, MCDR environment might not be probably setup
		file_missing = False

		def load(kind: str, func: Callable[[], Any], file_path: str) -> bool:
			nonlocal file_missing
			try:
				func()
			except FileNotFoundError:
				self.logger.error('{} file {!r} is missing'.format(kind.title(), file_path))
				file_missing = True
				return False
			except (YAMLError, ValueError) as e:
				self.logger.error('Failed to load {} file {!r}: {}'.format(kind, file_path, type(e).__name__))
				for line in str(e).splitlines():
					self.logger.error(line)
				return False
			else:
				return True

		# load_config: config, language, handlers, plugin directories, reactors, handlers
		# load_permission_file: permission
		# config change will lead to creating plugin folders
		loading_success = (
			load('configuration', lambda: self.load_config(allowed_missing_file=False, log=not args.initialize_environment), args.config_file_path) and
			load('permission', lambda: self.permission_manager.load_permission_file(allowed_missing_file=False), args.permission_file_path)
		)
		if file_missing:
			self.__on_file_missing()
			return
		if not loading_success:
			return

		# MCDR environment has been set up, so continue creating default folders and loading stuffs
		self.logger.set_file(core_constant.LOGGING_FILE)  # will create logs/ folder
		self.plugin_manager.touch_directory()  # will create config/ folder

		# --- Done --- #
		self.set_mcdr_state(MCDReforgedState.INITIALIZED)

	def __check_environment(self):
		"""
		Environment check at initialization. Warn and sleep if any of following conditions is met

		* mcdreforged package not found
		* current __file__ is not inside the mcdreforged package

		In dev environment, you can use setup.py to create `mcdreforged.egg-info/` so the package check can pass
		"""
		from_source_reason = None
		mcdr_pkg = core_constant.PACKAGE_NAME  # should be "mcdreforged"
		try:
			distribution = Distribution.from_name(mcdr_pkg)
		except PackageNotFoundError:
			from_source_reason = '{} distribution is not found in python packages'.format(mcdr_pkg)
		else:
			current_file = Path(__file__).absolute()
			dist_module_path = 'unknown'
			for file in distribution.files or []:
				dist_file = Path(file.locate())

				# find the mcdr_server.py in a mcdreforged directory in the distribution files
				if dist_file.name != current_file.name:
					continue

				dist_path = dist_file.parent
				if dist_path != dist_path.parent / mcdr_pkg:
					continue

				dist_module_path = dist_path
				try:
					if current_file.samefile(dist_file):
						break
				except OSError:
					pass
			else:
				from_source_reason = 'current source file ({}) is not in {} distribution module ({})'.format(current_file, mcdr_pkg, dist_module_path)

		if from_source_reason is not None:
			self.logger.warning('Looks like you\'re launching MCDR from source, since {}'.format(from_source_reason))
			self.logger.warning('In this way, the plugin system might not work correctly, and the maintainability of MCDR will be very poor')
			self.logger.warning('In a production environment, you should install {} from PyPI, NOT from source codes'.format(mcdr_pkg))
			self.logger.warning('See document ({}) for more information'.format(core_constant.DOCUMENTATION_URL))
			self.logger.warning('MCDR will launch after 20 seconds...')
			self.telemetry_reporter_scheduler.set_launched_from_source(True)
			time.sleep(20)

	def __on_file_missing(self):
		self.logger.info('Looks like MCDR is not initialized at current directory {}'.format(os.getcwd()))
		self.logger.info('Use command "{} init" to initialize MCDR first'.format(core_constant.CLI_COMMAND))
		self.logger.info('See document https://docs.mcdreforged.com/en/latest/quick_start.html#start-up')

	@property
	def config(self) -> MCDReforgedConfig:
		return self.config_manager.get_config()

	# --------------------------
	#         Translate
	# --------------------------

	def get_language(self) -> str:
		return self.translation_manager.language

	def translate(
			self, translation_key: str,
			*args,
			_mcdr_tr_language: Optional[str] = None,
			_mcdr_tr_fallback_language: Optional[str] = _UNSET,
			_mcdr_tr_allow_failure: bool = True,
			**kwargs
	) -> MessageText:
		"""
		Return a translated text corresponded to the translation key and format the text with given args
		If args contains RText element, then the result will be a RText, otherwise the result will be a regular str
		If the translation key is not recognized, the return value will be the translation key itself if allow_failure is True
		:param translation_key: The key of the translation
		:param args: The args to be formatted
		:param _mcdr_tr_language: Specific language to be used in this translation, or the language that MCDR is using will be used
		:param _mcdr_tr_fallback_language: The fallback language for another attempt, when the translation failed. Set it to None to disable auto-fallback
		:param _mcdr_tr_allow_failure: If set to false, a KeyError will be risen if the translation key is not recognized
		:param kwargs: The kwargs to be formatted
		"""
		if _mcdr_tr_fallback_language is _UNSET:
			fallback_handler = LanguageFallbackHandler.auto()
		elif _mcdr_tr_fallback_language is None:
			fallback_handler = LanguageFallbackHandler.none()
		else:
			fallback_handler = LanguageFallbackHandler.specified(_mcdr_tr_fallback_language)

		return self.translation_manager.translate(
			translation_key, args, kwargs,
			allow_failure=_mcdr_tr_allow_failure,
			language=_mcdr_tr_language,
			fallback_handler=fallback_handler,
			plugin_translations=self.plugin_manager.registry_storage.translations
		)

	def create_internal_translator(self, part: str) -> Translator:
		return Translator(('mcdreforged.' + part).rstrip('.'), mcdr_server=self)

	# --------------------------
	#          Loaders
	# --------------------------

	def load_config(self, *, allowed_missing_file: bool = True, log: bool = True):
		has_missing = self.config_manager.load(allowed_missing_file)
		# load the language before warning missing config to make sure translation is available
		self.on_config_changed(log=log)
		if log and has_missing:
			for line in self.translate('mcdreforged.config.missing_config').splitlines():
				self.logger.warning(line)

	def on_config_changed(self, *, log: bool):
		with self.__config_change_lock:
			config = self.config

			# update log settings first
			MCColorFormatControl.console_color_disabled = config.disable_console_color
			self.logger.set_debug_options(config.debug)

			# set language second, so mcdr can log with the expected language
			self.translation_manager.set_language(config.language)
			if log:
				self.logger.info(self.__tr('on_config_changed.language_set', config.language))

			if log and config.is_debug_on():
				self.logger.info(self.__tr('on_config_changed.debug_mode_on'))

			# applying other mcdr-scope stuffs
			self.__encoding_method = config.encoding or locale.getpreferredencoding()
			if not isinstance(config.decoding, list):
				self.__decoding_method = [config.decoding or locale.getpreferredencoding()]
			else:
				self.__decoding_method = config.decoding.copy()
			self.__decoding_method = collection_utils.unique_list(self.__decoding_method)
			if log:
				self.logger.info(self.__tr('on_config_changed.encoding_decoding_set', self.__encoding_method, ','.join(self.__decoding_method)))

			request_utils.set_proxies(config.http_proxy, config.https_proxy)
			self.connect_rcon()

			# trigger general config-changed callbacks
			for callback in self.__config_changed_callbacks:
				callback(config, log)

	def add_config_changed_callback(self, callback: _ConfigLoadedCallback):
		self.__config_changed_callbacks.append(callback)

	def load_plugins(self):
		future = self.plugin_manager.refresh_all_plugins()
		self.logger.info(future.result().to_rtext(self, show_path=True))

	def on_plugin_registry_changed(self):
		reg: 'PluginRegistryStorage' = self.plugin_manager.registry_storage
		with self.command_manager.start_command_register() as command_register:
			reg.export_commands(command_register)
		reg.export_server_handler(self.server_handler_manager.set_plugin_provided_server_handler_holder)

		info_filter_holders: List[InfoFilterHolder] = []
		reg.export_info_filters(info_filter_holders.append)
		self.reactor_manager.set_info_filters(info_filter_holders)

	# ---------------------------
	#      General Setters
	# ---------------------------
	# for field read-only access, simply use directly reference
	# but for field writing operation, use setters

	def set_task_executor(self, new_task_executor: SyncTaskExecutor):
		self.task_executor = new_task_executor

	# ---------------------------
	#   State Getters / Setters
	# ---------------------------

	def is_server_running(self) -> bool:
		return self.server_state.in_state(ServerState.RUNNING, ServerState.STOPPING)

	# Flags

	def is_server_startup(self) -> bool:
		return MCDReforgedFlag.SERVER_STARTUP in self.__flags

	def is_server_rcon_ready(self) -> bool:
		return MCDReforgedFlag.SERVER_RCON_READY in self.__flags

	def is_interrupt(self) -> bool:
		return MCDReforgedFlag.INTERRUPT in self.__flags

	def is_mcdr_exit(self) -> bool:
		return self.mcdr_in_state(MCDReforgedState.STOPPED)

	def is_mcdr_about_to_exit(self) -> bool:
		return self.mcdr_in_state(MCDReforgedState.PRE_STOPPED, MCDReforgedState.STOPPED)

	def should_exit_after_stop(self) -> bool:
		return MCDReforgedFlag.EXIT_AFTER_STOP in self.__flags

	def add_flag(self, flag: MCDReforgedFlag):
		self.__flags |= flag
		self.logger.mdebug('Added MCDReforgedFlag {}'.format(flag), option=DebugOption.MCDR)

	def remove_flag(self, flag: MCDReforgedFlag):
		self.__flags &= ~flag
		self.logger.mdebug('Removed MCDReforgedFlag {}'.format(flag), option=DebugOption.MCDR)

	# State

	def server_in_state(self, *states: ServerState) -> bool:
		return self.server_state.in_state(*states)

	def mcdr_in_state(self, *states: MCDReforgedState) -> bool:
		return self.mcdr_state.in_state(*states)

	def is_initialized(self) -> bool:
		return self.mcdr_in_state(MCDReforgedState.INITIALIZED)

	def set_server_state(self, state: ServerState):
		self.server_state = state
		self.logger.mdebug('Server state has set to {}'.format(state), option=DebugOption.MCDR)
		with self.server_state_cv:
			self.server_state_cv.notify_all()

	def set_mcdr_state(self, state: MCDReforgedState):
		self.mcdr_state = state
		self.logger.mdebug('MCDR state has set to {}'.format(state), option=DebugOption.MCDR)

	def should_keep_looping(self) -> bool:
		"""
		A criterion for sub threads to determine if it should keep looping
		:rtype: bool
		"""
		if self.server_in_state(ServerState.STOPPED):
			if self.is_interrupt():  # if interrupted and stopped
				return False
			if self.should_exit_after_stop():  # natural server stop, or server_interface.exit() by plugin
				return False
			return True
		return not self.is_mcdr_exit()

	# --------------------------
	#      Server Controls
	# --------------------------

	def start_server(self) -> bool:
		"""
		try to start the server process
		return True if the server process has started successfully
		return False if the server is not able to start
		"""
		with self.__starting_server_lock:
			if self.is_interrupt():
				self.logger.warning(self.__tr('start_server.already_interrupted'))
				return False
			if self.is_server_running():
				self.logger.warning(self.__tr('start_server.start_twice'))
				return False
			if self.is_mcdr_about_to_exit():
				self.logger.warning(self.__tr('start_server.about_to_exit'))
				return False

			cwd = Path(self.config.working_directory)
			if not cwd.is_dir():
				self.logger.error(self.__tr('start_server.cwd_not_existed', cwd))
				return False

			self.__on_server_start_pre()
			start_command = self.config.start_command
			self.logger.info(self.__tr('start_server.starting', repr(start_command)))
			try:
				self.process_manager.start(start_command, cwd=cwd)
			except Exception:
				self.logger.exception(self.__tr('start_server.start_fail'))
				return False
			else:
				self.__on_server_start_post()
				return True

	def __kill_server(self):
		"""
		Kill the server process group
		"""
		if self.process_manager.is_alive():
			self.logger.info(self.__tr('kill_server.killing'))
			self.process_manager.kill_process_tree()
		else:
			self.logger.warning('Try to kill the server when the server process has already been terminated')

	def interrupt(self) -> bool:
		"""
		Interrupt MCDR
		The first call will softly stop the server and the later calls will kill the server
		Return if it's the first try
		"""
		first_interrupt = not self.is_interrupt()
		self.logger.info(self.__tr('interrupt.{}'.format('soft' if first_interrupt else 'hard')))
		if self.is_server_running():
			self.stop(forced=not first_interrupt)
		self.add_flag(MCDReforgedFlag.INTERRUPT)
		return first_interrupt

	def stop(self, forced: bool = False) -> bool:
		"""
		Stop the server

		:param forced: an optional bool. If it's False (default) MCDR will stop the server by sending the STOP_COMMAND from the
		current handler. If it's True MCDR will just kill the server process group
		"""
		with self.__stop_lock:
			if not self.is_server_running():
				self.logger.warning(self.__tr('stop.stop_when_stopped'))
				return False
			self.set_server_state(ServerState.STOPPING)
			if not forced:
				try:
					self.send(self.server_handler_manager.get_current_handler().get_stop_command())
				except Exception:
					self.logger.error(self.__tr('stop.stop_fail'))
					forced = True
			if forced:
				self.__kill_server()
			return True

	# --------------------------
	#      Server Logics
	# --------------------------

	def __on_server_start_pre(self):
		# we might be on the task executor thread, so we cannot use policy=always_new_task with block=True, or self-join will happen
		self.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_START_PRE, (), dispatch_policy=self.plugin_manager.DispatchEventPolicy.ensure_on_thread, block=True)

	def __on_server_start_post(self):
		self.set_server_state(ServerState.RUNNING)
		self.add_flag(MCDReforgedFlag.EXIT_AFTER_STOP)  # Set after server state is set to RUNNING, or MCDR might have a chance to exit if the server is started by other thread
		self.logger.info(self.__tr('start_server.pid_info', self.process_manager.get_pid()))
		self.reactor_manager.on_server_start()
		self.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_START, ())

	def __on_server_stop(self):
		return_code = self.process_manager.get_return_code()
		if return_code >= 0:
			self.logger.info(self.__tr('on_server_stop.show_return_code', return_code))
		else:
			self.logger.info(self.__tr('on_server_stop.show_return_code_signal', return_code, os_utils.get_signal_name(-return_code)))
		self.process_manager.reset()
		self.set_server_state(ServerState.STOPPED)
		self.remove_flag(MCDReforgedFlag.SERVER_STARTUP | MCDReforgedFlag.SERVER_RCON_READY)  # removes this two
		self.reactor_manager.on_server_stop()
		if self.is_interrupt():
			self.logger.info(self.__tr('on_server_stop.user_interrupted'))
		else:
			self.logger.info(self.__tr('on_server_stop.server_stop'))

		self.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_STOP, (return_code,), block=True)

	def send(self, text: str, ending: str = '\n', encoding: Optional[str] = None):
		"""
		Send a text to server's stdin if the server is running

		:param text: A str or a bytes you want to send. if text is a str then it will attach the ending parameter to its
		back
		:param str ending: The suffix of a command with a default value \n
		:param str encoding: The encoding method for the text. If it's not given used the method in config
		"""
		if encoding is None:
			encoding = self.__encoding_method
		if isinstance(text, str):
			encoded_text = (text + ending).encode(encoding)
		else:
			raise TypeError('should be a str, found {}'.format(type(text)))
		if self.is_server_running():
			self.process_manager.write(encoded_text)
		else:
			self.logger.warning(self.__tr('send.send_when_stopped'))
			self.logger.warning(self.__tr('send.send_when_stopped.text', repr(text) if len(text) <= 32 else repr(text[:32]) + '...'))

	def __receive(self) -> _ParsedServerOutput:
		"""
		Try to receive a str from server's stdout. This will block the current thread

		If server has stopped it will wait up to 60s for the server process to exit

		:raise _ServerProcessStopped: The server has stopped
		:raise _ReceiveDecodeError: Decode error
		"""
		so = self.process_manager.read_line()
		if so is None:
			raise _ServerProcessStopped()

		line_buf: bytes = so.line
		errors: Dict[str, UnicodeError] = {}
		for enc in self.__decoding_method:
			try:
				line_text: str = line_buf.decode(enc)
			except UnicodeError as e:  # https://docs.python.org/3/library/codecs.html#error-handlers
				errors[enc] = e
			else:
				return _ParsedServerOutput(line_text.strip('\n\r'), so.is_stdout)
		self.logger.error(self.__tr('receive.decode_fail', line_buf, errors))
		raise _ReceiveDecodeError()

	def __tick(self):
		"""
		ticking MCDR:
		try to receive a new line from server's stdout and parse / display / process the text
		"""
		try:
			recv_result = self.__receive()
		except _ReceiveDecodeError:
			return
		except _ServerProcessStopped:
			self.__on_server_stop()
			return

		# TODO: make use of recv_result.is_stdout
		text: str = recv_result.line
		try:
			text = self.server_handler_manager.get_current_handler().pre_parse_server_stdout(text)
		except Exception:
			self.logger.warning(self.__tr('tick.pre_parse_fail'))

		info: Info
		try:
			info = self.server_handler_manager.get_current_handler().parse_server_stdout(text)
		except Exception:
			if self.logger.should_log_debug(option=DebugOption.HANDLER):  # traceback.format_exc() is costly
				self.logger.mdebug('Fail to parse text {!r} from stdout of the server, using raw handler'.format(text), no_check=True)
				for line in traceback.format_exc().splitlines():
					self.logger.mdebug('    {}'.format(line), no_check=True)
			info = self.server_handler_manager.get_basic_handler().parse_server_stdout(text)
		else:
			if self.logger.should_log_debug(option=DebugOption.HANDLER):
				self.logger.mdebug('Parsed text from server stdout: {}'.format(info), no_check=True)
		self.server_handler_manager.detect_text(text)

		self.reactor_manager.put_info(info)

	def __on_mcdr_start(self):
		self.logger.info(self.__tr('on_mcdr_start.starting', core_constant.NAME, core_constant.VERSION))
		self.__register_signal_handler()
		self.watch_dog.start()
		self.telemetry_reporter_scheduler.start()
		self.task_executor.start()
		self.async_task_executor.start()
		self.preference_manager.load_preferences()
		self.plugin_manager.register_builtin_plugins()
		self.task_executor.submit(self.load_plugins).result()
		self.plugin_manager.dispatch_event(MCDRPluginEvents.MCDR_START, ())
		if not self.config.disable_console_thread:
			self.console_handler.start()
		else:
			self.logger.info(self.__tr('on_mcdr_start.console_disabled'))
		if self.__no_server_start:
			self.logger.info('Server start skipped')
		else:
			if not self.start_server():
				raise ServerStartError()
		self.update_helper.start()
		if self.config.handler_detection:
			self.server_handler_manager.start_handler_detection()
		self.set_mcdr_state(MCDReforgedState.RUNNING)

	def __register_signal_handler(self):
		do_callback_lock = threading.Lock()

		def do_callback(sig: int):
			signal_name = os_utils.get_signal_name(sig)

			if not do_callback_lock.acquire(blocking=False):
				self.logger.mdebug('Received signal {} ({}), do_callback_lock not acquired, skip'.format(signal_name, sig), option=DebugOption.MCDR)
				return
			try:
				self.logger.warning('Received signal {} ({}), interrupting MCDR'.format(signal_name, sig))
				self.interrupt()
			finally:
				do_callback_lock.release()

		def callback(sig: int, _frame):
			# never do logging inside the signal handler. Nobody wants reentrant logging calls
			thread_utils.start_thread(do_callback, (sig,), f'SignalHandler')

		import signal
		signal.signal(signal.SIGINT, callback)   # ctrl + c
		signal.signal(signal.SIGTERM, callback)  # graceful termination

	def __on_mcdr_stop(self):
		try:
			self.set_mcdr_state(MCDReforgedState.PRE_STOPPED)
			self.logger.info(self.__tr('on_mcdr_stop.info'))

			with self.watch_dog.pausing():  # it's ok for plugins to take some time
				self.plugin_manager.dispatch_event(MCDRPluginEvents.MCDR_STOP, ())
				self.plugin_manager.dispatch_event(MCDRPluginEvents.PLUGIN_UNLOADED, ())

				def join_executor(executor: BackgroundThreadExecutor):
					wait_sec = 10 if self.is_interrupt() else 1800
					for i in range(wait_sec):
						executor.join(timeout=1)
						if executor.get_thread().is_alive():
							if (sec := i + 1) in [10, 30, 60, 120, 300, 600, 1800]:
								self.logger.warning('{} is still alive after {} seconds, stack trace:'.format(executor, sec))
								if (ss := executor.get_thread_stack()) is not None:
									for line in ss.get_lines():
										self.logger.warning(line)
						else:
							break
					else:
						self.logger.warning('No more waiting after {} seconds, exit anyway'.format(wait_sec))

				self.task_executor.soft_stop()
				join_executor(self.task_executor)

				# Stop sync executor after the sync task executor, for best effort on processing all submitted coro
				# to prevent "coroutine xxx was never awaited" from happening
				self.async_task_executor.stop()
				join_executor(self.async_task_executor)

				self.watch_dog.stop()
				join_executor(self.watch_dog)

			self.console_handler.stop()
			self.update_helper.stop()
			self.telemetry_reporter_scheduler.stop()
			self.logger.info(self.__tr('on_mcdr_stop.bye'))
		except KeyboardInterrupt:  # I don't know why there sometimes will be a KeyboardInterrupt if MCDR is stopped by ctrl-c
			pass
		except Exception:
			self.logger.exception(self.__tr('on_mcdr_stop.stop_error'))
		finally:
			self.set_mcdr_state(MCDReforgedState.STOPPED)

	def run_mcdr(self):
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
		self.__main_loop()

	def __main_loop(self):
		"""
		The main loop of MCDR
		"""
		self.__on_mcdr_start()
		while self.should_keep_looping():
			try:
				if self.is_server_running():
					self.__tick()
				else:
					with self.server_state_cv:
						self.server_state_cv.wait(0.01)
			except KeyboardInterrupt:
				self.interrupt()
			except Exception:
				if self.is_interrupt():
					break
				else:
					self.logger.critical(self.__tr('run.error'), exc_info=True)
		self.__on_mcdr_stop()

	def connect_rcon(self):
		self.rcon_manager.disconnect()
		rcon_config = self.config.rcon
		if rcon_config.enable and self.is_server_rcon_ready():
			self.rcon_manager.connect(
				address=rcon_config.address,
				port=rcon_config.port,
				password=rcon_config.password,
			)
