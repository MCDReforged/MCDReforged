import asyncio
import inspect
import logging
import threading
from concurrent.futures import Future
from pathlib import Path
from typing import Callable, TYPE_CHECKING, Tuple, Any, Union, Optional, List, Dict, overload, Literal, Coroutine, TypeVar

import psutil

from mcdreforged.command.command_source import CommandSource, PluginCommandSource, PlayerCommandSource, ConsoleCommandSource
from mcdreforged.constants.deprecations import SERVER_INTERFACE_LANGUAGE_KEYWORD
from mcdreforged.info_reactor.info import Info, InfoSource
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.mcdr_state import MCDReforgedFlag
from mcdreforged.permission.permission_level import PermissionLevel, PermissionParam
from mcdreforged.plugin import plugin_factory
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.operation_result import PluginOperationResult, PluginResultType
from mcdreforged.plugin.plugin_event import PluginEvent, MCDRPluginEvents
from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.plugin import AbstractPlugin
from mcdreforged.preference.preference_manager import PreferenceItem
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_utils, file_utils, class_utils, future_utils
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.types.message import MessageText
from mcdreforged.utils.types.path_like import PathStr

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.handler.server_handler import ServerHandler
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.si.plugin_server_interface import PluginServerInterface
	from mcdreforged.plugin.type.regular_plugin import RegularPlugin


_T = TypeVar('_T')


class ServerInterface:
	"""
	ServerInterface is the interface with lots of API for plugins to interact with the server.
	Its subclass :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface`
	contains extra APIs for plugins to control the plugin itself

	It's recommend to use ``server`` as the variable name of the ServerInterface. This is widely used in this document
	"""

	MCDR = True
	"""An identifier field for MCDR"""

	__global_instance: Optional['ServerInterface'] = None  # For singleton instance storage

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self._mcdr_server: 'MCDReforgedServer' = mcdr_server
		self._tr = mcdr_server.create_internal_translator('server_interface')
		if type(self) is ServerInterface:
			# singleton, should only occur during MCDReforgedServer construction
			if ServerInterface.__global_instance is not None:
				self._mcdr_server.logger.warning('Double assigning the singleton instance in {}'.format(self.__class__.__name__), stack_info=True)
			ServerInterface.__global_instance = self

	@property
	def _plugin_manager(self) -> 'PluginManager':
		return self._mcdr_server.plugin_manager

	def _create_plugin_logger(self, plugin_id: str) -> MCDReforgedLogger:
		logger = MCDReforgedLogger(plugin_id)
		logger.addHandler(self._mcdr_server.logger.file_handler)
		return logger

	@property
	def logger(self) -> logging.Logger:
		"""
		A nice logger for you to log message to the console
		"""
		plugin = self._plugin_manager.get_plugin_in_current_context()
		if plugin is not None:
			return self._create_plugin_logger(plugin.get_id())
		else:
			return self._mcdr_server.logger

	# ------------------------
	#    Instance Getters
	# ------------------------

	@classmethod
	def get_instance(cls) -> Optional['ServerInterface']:
		"""
		A class method, for plugins to get a ServerInterface instance anywhere as long as MCDR is running
		"""
		return cls.__global_instance

	def as_basic_server_interface(self) -> 'ServerInterface':
		"""
		Return a :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` instance.
		The type of the return value is exactly the :class:`~mcdreforged.plugin.si.server_interface.ServerInterface`

		It's used for removing the plugin information inside :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface`
		when you need to send a :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` as parameter
		"""
		return self.get_instance()

	def as_plugin_server_interface(self) -> Optional['PluginServerInterface']:
		"""
		Return a :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` instance.

		If the object is exactly a :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` instance, return itself

		If the plugin context is available, return the :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` for the related plugin.
		Currently, plugin context is only available inside the following scenarios:

		1.  :ref:`Plugin entrypoint <plugin-entrypoint>` module loading
		2.  :doc:`Event listener </plugin_dev/event>` callback invocation
		3.  :doc:`Command </plugin_dev/command>` callback invocation
		"""
		plugin = self._plugin_manager.get_plugin_in_current_context()
		if plugin is not None:
			return plugin.server_interface
		return None

	@classmethod
	def si(cls) -> 'ServerInterface':
		"""
		Alias / Shortform of :meth:`get_instance`,
		and never returns None

		:raise RuntimeError: If MCDR is not running
		"""
		si = cls.get_instance()
		if si is None:
			raise RuntimeError('get ServerInterface failed, MCDR is not running')
		return si

	@classmethod
	def si_opt(cls) -> Optional['ServerInterface']:
		"""
		Alias / Shortform of :meth:`get_instance`,
		get an optional :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` instance

		:return: The :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` instance, or None if failed
		"""
		return cls.get_instance()

	@classmethod
	def psi(cls) -> 'PluginServerInterface':
		"""
		Shortform of the combination of :meth:`get_instance` + :meth:`as_plugin_server_interface`,
		and never returns None

		:raise RuntimeError: Get :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` failed. This might occur because
			MCDR is not running (see :meth:`si`),
			or plugin context is unavailable (see :meth:`as_plugin_server_interface`)
		"""
		psi = cls.si().as_plugin_server_interface()
		if psi is None:
			raise RuntimeError('get PluginServerInterface failed, current thread {} does not contain enough plugin context'.format(threading.current_thread()))
		return psi

	@classmethod
	def psi_opt(cls) -> Optional['PluginServerInterface']:
		"""
		Shortform of the combination of :meth:`get_instance` + :meth:`as_plugin_server_interface`,
		get an optional :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` instance

		:return: The :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` instance for the current plugin, or None if failed
		"""
		si = cls.get_instance()
		if si is not None:
			return si.as_plugin_server_interface()
		return None

	# ------------------------
	#          Utils
	# ------------------------

	def tr(self, translation_key: str, *args, _mcdr_tr_language: Optional[str] = None, language: Optional[str] = None, **kwargs) -> MessageText:
		"""
		Return a translated text corresponded to the translation key and format the text with given args and kwargs

		If args or kwargs contains :class:`RText <mcdreforged.minecraft.rtext.text.RTextBase>` element,
		then the result will be a :class:`RText <mcdreforged.minecraft.rtext.text.RTextBase>`,
		otherwise the result will be a regular str

		If the translation key is not recognized, the return value will be the translation key itself

		See :ref:`here <plugin-translation>` for the ways to register translations for your plugin

		:param translation_key: The key of the translation
		:param args: The args to be formatted
		:param _mcdr_tr_language: Specific language to be used in this translation, or the language that MCDR is using will be used
		:param language: Deprecated, to be removed in v2.15. Use kwarg *_mcdr_tr_language* instead
		:param kwargs: The kwargs to be formatted
		"""
		if language is not None and _mcdr_tr_language is None:
			self.logger.warning('%s. Translation key: %s', SERVER_INTERFACE_LANGUAGE_KEYWORD, translation_key)
			_mcdr_tr_language = language

		return self._mcdr_server.translate(translation_key, *args, _mcdr_tr_language=_mcdr_tr_language, **kwargs)

	def rtr(self, translation_key: str, *args, **kwargs) -> RTextMCDRTranslation:
		"""
		Return a :class:`~mcdreforged.translation.translation_text.RTextMCDRTranslation` component,
		that only translates itself right before displaying or serializing

		Using this method instead of :meth:`tr` allows you to display your texts in :ref:`user's preferred language <preference-language>` automatically

		Of course, you can construct :class:`~mcdreforged.translation.translation_text.RTextMCDRTranslation` yourself instead of using this method if you want

		:param translation_key: The key of the translation
		:param args: The args to be formatted
		:param kwargs: The kwargs to be formatted

		.. versionadded:: v2.1.0
		"""
		text = RTextMCDRTranslation(translation_key, *args, **kwargs)
		text.set_translator(self.tr)  # not that necessary tbh, just in case self.tr != ServerInterface.get_instance().tr somehow
		return text

	def has_translation(self, translation_key: str, *, language: Optional[str] = None, no_auto_fallback: bool = False):
		"""
		Check if the given translation exists

		Notes that if the current language fails, MCDR will try to use "en_us" for a second attempt.
		If you don't want this auto-fallback behavior, set argument *no_auto_fallback* to True

		Also, you don't need to pass ``*args`` and ``**kwargs`` for the translation into this method,
		because existence check doesn't need those

		:param translation_key: The key of the translation
		:keyword language: Optional, the language to check for translation key existence
		:keyword no_auto_fallback: When set to True, MCDR will not fall back to "en_us" and have another translation try, if translation failed

		.. versionadded:: v2.12.0
		"""
		kwargs = dict(
			_mcdr_tr_language=language,
			_mcdr_tr_allow_failure=False
		)
		if no_auto_fallback:
			kwargs.update(_mcdr_tr_fallback_language=None)
		try:
			self._mcdr_server.translate(translation_key, **kwargs)
		except KeyError:
			return False
		else:
			return True

	# ------------------------
	#      Server Control
	# ------------------------

	def start(self) -> bool:
		"""
		Start the server. Return if the action succeed.

		If the server is running or being starting by other plugin it will return ``False``

		:return: If the operation succeed.
			The operation fails if the server is already started, or cannot start due to invalid command or current MCDR state
		"""
		return self._mcdr_server.start_server()

	def stop(self) -> bool:
		"""
		Soft shutting down the server by sending the correct stop command to the server

		This option will not stop MCDR. MCDR will keep running unless :meth:`exit` is invoked

		:return: If the operation succeed.
			The operation fails if the server is already stopped
		"""
		self._mcdr_server.remove_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
		return self._mcdr_server.stop(forced=False)

	def kill(self) -> bool:
		"""
		Kill the entire server process group. A hard shutting down

		MCDR will keep running unless :meth:`exit` is invoked

		:return: If the operation succeed.
			The operation fails if the server is already stopped
		"""
		return self._mcdr_server.stop(forced=True)

	def wait_until_stop(self) -> None:
		"""
		Wait until the server is stopped

		.. note:: The current thread will be blocked
		"""
		cv = self._mcdr_server.server_state_cv
		with cv:
			while self.is_server_running():
				cv.wait(0.1)

	def wait_for_start(self) -> None:
		"""
		Wait until the server is able to start

		Actually it's an alias of :meth:`wait_until_stop`
		"""
		self.wait_until_stop()

	def restart(self) -> bool:
		"""
		Restart the server

		It will first :meth:`soft stop <stop>` the server
		and then :meth:`wait <wait_for_start>` until the server is stopped,
		finally :meth:`start <start>` the server up

		:return: If the operation succeed.
			The operation fails if the server is already stopped
		"""
		if not self.stop():
			return False
		self.wait_for_start()
		return self.start()

	def stop_exit(self) -> bool:
		"""
		:meth:`soft stop <stop>` the server and exit MCDR

		:return: If the operation succeed.
			The operation fails if the server is already stopped
		"""
		ok = self._mcdr_server.stop(forced=False)
		if ok:
			self._mcdr_server.add_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
		return ok

	def exit(self) -> bool:
		"""
		Exit MCDR when the server is stopped

		Basically it's the same to invoking :meth:`set_exit_after_stop_flag` with parameter ``True``,
		but with an extra server not running check

		Example usage::

			server.stop()  # Stop the server
			# do something A
			server.wait_for_start()  # Make sure the server is fully stopped. It's necessary to run it in your custom thread
			# do something B
			server.exit()  # Exit MCDR

		:return: If the operation succeed.
			The operation fails if the server is still running
		"""
		if self._mcdr_server.is_server_running():
			return False
		self._mcdr_server.add_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
		return True

	def set_exit_after_stop_flag(self, flag_value: bool) -> None:
		"""
		Set the flag that indicating if MCDR should exit when the server has stopped

		If set to ``True``, after the server stops MCDR will exit, otherwise (set to ``False``) MCDR will just keep running

		The flag value will be set to ``True`` everytime when the server starts

		The flag value is displayed in line 5 in command ``!!MCDR status``
		"""
		if flag_value:
			self._mcdr_server.add_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
		else:
			self._mcdr_server.remove_flag(MCDReforgedFlag.EXIT_AFTER_STOP)

	def is_server_running(self) -> bool:
		"""
		Return if the server is running
		"""
		return self._mcdr_server.is_server_running()

	def is_server_startup(self) -> bool:
		"""
		Return if the server has started up
		"""
		return self._mcdr_server.is_server_startup()

	def is_rcon_running(self) -> bool:
		"""
		Return if MCDR's rcon is running
		"""
		return self._mcdr_server.rcon_manager.is_running()

	def get_server_pid(self) -> Optional[int]:
		"""
		Return the pid of the server process

		Notes the process with this pid is a bash process, which is the parent process of real server process
		you might be interested in

		:return: The pid of the server. None if the server is stopped
		"""
		return self._mcdr_server.process_manager.get_pid()

	def get_server_pid_all(self) -> List[int]:
		"""
		Return a list of pid of all processes in the server's process group

		:return: A list of pid. It will be empty if the server is stopped or the pid query failed

		.. versionadded:: v2.6.0
		"""
		pids: List[int] = []
		root_pid = self.get_server_pid()
		if root_pid is not None:
			try:
				pids.append(root_pid)
				for process in psutil.Process(root_pid).children(recursive=True):
					pids.append(process.pid)
			except psutil.NoSuchProcess:
				pids.clear()
		return pids

	def get_server_information(self) -> ServerInformation:
		"""
		Return a :class:`~mcdreforged.info_reactor.server_information.ServerInformation` object indicating
		the information of the current server, interred from the output of the server

		It's field(s) might be None if the server is offline, or the related information has not been parsed

		.. versionadded:: v2.1.0
		"""
		return self._mcdr_server.server_information.copy()

	# ------------------------
	#     Text Interaction
	# ------------------------

	def execute(self, text: str, *, encoding: Optional[str] = None) -> None:
		"""
		Execute a server command by sending the command content to server's standard input stream

		.. seealso::

			:meth:`execute_command` if you want to execute command in MCDR's command system

		:param text: The content of the command you want to send
		:keyword encoding: The encoding method for the text.
			Leave it empty to use the encoding method from the configuration of MCDR
		"""
		logger = self.logger
		if isinstance(logger, MCDReforgedLogger):  # make type checker happy
			logger.mdebug('Sending command {!r}'.format(text), option=DebugOption.PLUGIN)
		self._mcdr_server.send(text, encoding=encoding)

	@property
	def __server_handler(self) -> 'ServerHandler':
		return self._mcdr_server.server_handler_manager.get_current_handler()

	def tell(self, player: str, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Use command like ``/tellraw`` to send the message to the specific player

		:param player: The name of the player you want to tell
		:param text: The message you want to send to the player
		:keyword encoding: The encoding method for the text.
			Leave it empty to use the encoding method from the configuration of MCDR
		"""
		with RTextMCDRTranslation.language_context(self._mcdr_server.preference_manager.get_preferred_language(player)):
			command = self.__server_handler.get_send_message_command(player, text, self.get_server_information())
		if command is not None:
			self.execute(command, encoding=encoding)

	def say(self, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Use command like ``/tellraw @a`` to broadcast the message in game

		:param text: The message you want to send
		:keyword encoding: The encoding method for the text.
			Leave it empty to use the encoding method from the configuration of MCDR
		"""
		command = self.__server_handler.get_broadcast_message_command(text, self.get_server_information())
		if command is not None:
			self.execute(command, encoding=encoding)

	def broadcast(self, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Broadcast the message in game and to the console

		If the server is not running, send the message to console only

		:param text: The message you want to send
		:keyword encoding: The encoding method for the text.
			Leave it empty to use the encoding method from the configuration of MCDR
		"""
		if self.is_server_running():
			self.say(text, encoding=encoding)
		with RTextMCDRTranslation.language_context(self._mcdr_server.preference_manager.get_console_preference().language):
			misc_utils.print_text_to_console(self.logger, text)

	# noinspection PyMethodMayBeStatic
	def reply(self, info: Info, text: MessageText, *, encoding: Optional[str] = None, console_text: Optional[MessageText] = None):
		"""
		Reply to the source of the Info

		If the Info is from a player, then use tell to reply the player;
		if the Info is from the console, then use ``server.logger.info`` to output to the console;
		In the rest of the situations, the Info is not from a user,
		a :class:`~mcdreforged.utils.exception.IllegalCallError` is raised

		:param info: the Info you want to reply to
		:param text: The message you want to send
		:keyword encoding: The encoding method for the text
		:keyword console_text: If it's specified, *console_text* will be used instead of text when replying to console
		:raise IllegalCallError: If the Info is not from a user
		"""
		source = info.get_command_source()
		if source is None:
			raise IllegalCallError('Cannot reply to the given info instance')
		source.reply(text, encoding=encoding, console_text=console_text)

	# ------------------------
	#      Plugin Queries
	# ------------------------

	@overload
	def __existed_plugin_info_getter(self, plugin_id: str, handler: Callable[['RegularPlugin'], Any], *, regular: Literal[True]): ...
	@overload
	def __existed_plugin_info_getter(self, plugin_id: str, handler: Callable[['AbstractPlugin'], Any], *, regular: Literal[False]): ...

	def __existed_plugin_info_getter(self, plugin_id: str, handler: Callable[['AbstractPlugin'], Any], *, regular: bool):
		if regular:
			plugin = self._plugin_manager.get_regular_plugin_from_id(plugin_id)
		else:
			plugin = self._plugin_manager.get_plugin_from_id(plugin_id)
		if plugin is not None:
			return handler(plugin)
		return None

	def get_plugin_metadata(self, plugin_id: str) -> Optional[Metadata]:
		"""
		Return the metadata of the specified plugin, or None if the plugin doesn't exist

		:param plugin_id: The id of the plugin to query metadata
		"""
		def getter(plugin: AbstractPlugin) -> Metadata:
			return plugin.get_metadata()
		return self.__existed_plugin_info_getter(plugin_id, getter, regular=False)

	def get_plugin_type(self, plugin_id: str) -> Optional[PluginType]:
		"""
		Return the type of the specified plugin, or None if the plugin doesn't exist

		:param plugin_id: The id of the plugin to query type

		.. versionadded:: v2.13.0
		"""
		def getter(plugin: 'AbstractPlugin') -> PluginType:
			return plugin.get_type()
		return self.__existed_plugin_info_getter(plugin_id, getter, regular=False)

	def get_plugin_file_path(self, plugin_id: str) -> Optional[str]:
		"""
		Return the file path of the specified plugin, or None if the plugin doesn't exist

		:param plugin_id: The id of the plugin to query file path
		"""
		def getter(plugin: 'RegularPlugin') -> str:
			return str(plugin.file_path)
		return self.__existed_plugin_info_getter(plugin_id, getter, regular=True)

	def is_plugin_file_changed(self, plugin_id: str) -> Optional[bool]:
		"""
		Return if the given plugin has its plugin file changed,
		or None if the plugin doesn't exist

		Notes: :ref:`plugin_dev/plugin_format:Directory Plugin` is always considered as changed

		:param plugin_id: The id of the plugin to query file change state

		.. versionadded:: v2.13.0
		"""
		def getter(plugin: 'RegularPlugin') -> bool:
			return plugin.file_changed()
		return self.__existed_plugin_info_getter(plugin_id, getter, regular=True)

	def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
		"""
		Return the :ref:`entrypoint <plugin-entrypoint>` module instance of the specific plugin,
		or None if the plugin doesn't exist

		If the target plugin is a :ref:`solo plugin <plugin-format-solo>` and it needs to react to events from MCDR,
		it's quite important to use this instead of manually import the plugin you want,
		since it's the only way to make your plugin be able to access the same plugin instance to MCDR

		Example usage:

			The entrypoint module of my API plugin with id ``my_api``::

				def some_api(item):
					pass

			Another plugin that needs my API plugin::

				server.get_plugin_instance('my_api').some_api(an_item)

		:param plugin_id: The id of the plugin you want to get entrypoint module instance
		:return: A entrypoint module instance, or None if the plugin doesn't exist
		"""
		def getter(plugin: 'RegularPlugin') -> Any:
			return plugin.entry_module_instance
		return self.__existed_plugin_info_getter(plugin_id, getter, regular=True)

	def get_plugin_list(self) -> List[str]:
		"""
		Return a list containing all **loaded** plugin id like ``["my_plugin", "another_plugin"]``
		"""
		return [plugin.get_id() for plugin in self._plugin_manager.get_regular_plugins()]

	def __get_files_in_plugin_directories(self) -> List[str]:
		result: List[Path] = []
		for plugin_directory in self._plugin_manager.plugin_directories:
			result.extend(file_utils.list_all(plugin_directory))
		return list(map(str, result))

	def get_unloaded_plugin_list(self) -> List[str]:
		"""
		Return a list containing all **unloaded** plugin file path like ``["plugins/MyPlugin.mcdr"]``

		.. versionadded:: v2.3.0
		"""
		def predicate(file_path: str) -> bool:
			return not self._plugin_manager.contains_plugin_file(file_path) and plugin_factory.is_plugin(file_path)
		return list(filter(predicate, self.__get_files_in_plugin_directories()))

	def get_disabled_plugin_list(self) -> List[str]:
		"""
		Return a list containing all **disabled** plugin file path like ["plugins/MyPlugin.mcdr.disabled"]

		.. versionadded:: v2.3.0
		"""
		def predicate(file_path: str) -> bool:
			return plugin_factory.is_disabled_plugin(file_path)
		return list(filter(predicate, self.__get_files_in_plugin_directories()))

	def get_all_metadata(self) -> Dict[str, Metadata]:
		"""
		Return a dict containing metadata of all loaded plugin with (plugin_id, metadata) as key-value pair
		"""
		result = {}
		for plugin in self._plugin_manager.get_all_plugins():
			result[plugin.get_id()] = plugin.get_metadata()
		return result

	# ------------------------
	#     Plugin Operations
	# ------------------------

	# Notes: All plugin manipulation will trigger a dependency check, which might cause unwanted plugin operations

	def __not_loaded_regular_plugin_manipulate(
			self,
			plugin_file_path: PathStr,
			handler: Callable[['PluginManager'], Callable[[Path], 'Future[PluginOperationResult]']]
	) -> bool:
		"""
		Manipulate a not loaded regular plugin from a given file path
		:param plugin_file_path: The path to the not loaded new plugin
		:param handler: What you want to do with Plugin Manager to the given file path
		:return: If success
		"""
		plugin_file_path = Path(plugin_file_path)
		future: 'Future[PluginOperationResult]' = handler(self._plugin_manager)(plugin_file_path)
		if future.done():
			return future.result().get_if_success(PluginResultType.LOAD)  # the operations are always loading a plugin
		else:
			return False  # TODO handle unknown result caused by chained sync plugin operation

	def __existed_regular_plugin_manipulate(
			self,
			plugin_id: str,
			handler: Callable[['PluginManager'], Callable[['RegularPlugin'], 'Future[PluginOperationResult]']],
			result_type: PluginResultType
	) -> Optional[bool]:
		"""
		Manipulate a loaded regular plugin from a given plugin id
		:param plugin_id: The plugin id of the plugin you want to manipulate
		:param handler: What callable you want to use with Plugin Manager to the plugin id,
		the returned callable accepts the plugin instance
		:param result_type: The type of the result. It's used to determine how to get the single operation result from the plugin operation result.
		It's used to determine if the operation succeeded
		:return: If success, None if plugin not found
		"""
		plugin = self._plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			future = handler(self._plugin_manager)(plugin)
			if future.done():
				return future.result().get_if_success(result_type)
			else:
				return None
		return None

	def __plugin_operation_thread_check(self):
		# The PLUGIN_LOADED and PLUGIN_UNLOADED event listeners during plugin manipulation
		# are required to be triggered serially. The listener callback might be an async function,
		# meaning that we need to be on the non-AsyncTaskExecutor thread to blockingly invoke it.
		if self.is_on_async_executor_thread():
			raise RuntimeError('You can not perform plugin operations directly on the {} thread'.format(threading.current_thread().name))

	def load_plugin(self, plugin_file_path: str) -> bool:
		"""
		Load a plugin from the given file path

		:param plugin_file_path: The file path of the plugin to load. Example: "plugins/my_plugin.py"
		:return: If the plugin gets loaded successfully
		"""
		def get_handler(mgr: 'PluginManager'):
			return mgr.load_plugin

		self.__plugin_operation_thread_check()
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, get_handler)

	def enable_plugin(self, plugin_file_path: str) -> bool:
		"""
		Enable a disabled plugin from the given path

		:param plugin_file_path: The file path of the plugin to enable. Example: "plugins/my_plugin.py.disabled"
		:return: If the plugin gets enabled successfully
		"""
		def get_handler(mgr: 'PluginManager'):
			return mgr.enable_plugin

		self.__plugin_operation_thread_check()
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, get_handler)

	def reload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Reload a plugin specified by plugin id

		:param plugin_id: The id of the plugin to reload. Example: ``"my_plugin"``
		:return: A bool indicating if the plugin gets reloaded successfully, or None if plugin not found
		"""
		def get_handler(mgr: 'PluginManager'):
			return mgr.reload_plugin

		self.__plugin_operation_thread_check()
		return self.__existed_regular_plugin_manipulate(plugin_id, get_handler, PluginResultType.RELOAD)

	def unload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Unload a plugin specified by plugin id

		:param plugin_id: The id of the plugin to unload. Example: ``"my_plugin"``
		:return: A bool indicating if the plugin gets unloaded successfully, or None if plugin not found
		"""
		def get_handler(mgr: 'PluginManager'):
			return mgr.unload_plugin

		self.__plugin_operation_thread_check()
		return self.__existed_regular_plugin_manipulate(plugin_id, get_handler, PluginResultType.UNLOAD)

	def disable_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Disable an unloaded plugin specified by plugin id

		:param plugin_id: The id of the plugin to disable. Example: ``"my_plugin"``
		:return: A bool indicating if the plugin gets disabled successfully, or None if plugin not found
		"""
		def get_handler(mgr: 'PluginManager'):
			return mgr.disable_plugin

		self.__plugin_operation_thread_check()
		return self.__existed_regular_plugin_manipulate(plugin_id, get_handler, PluginResultType.UNLOAD)

	def refresh_all_plugins(self) -> None:
		"""
		Reload all plugins, load all new plugins and then unload all removed plugins
		"""
		self.__plugin_operation_thread_check()
		self._plugin_manager.refresh_all_plugins()

	def refresh_changed_plugins(self) -> None:
		"""
		Reload all **changed** plugins, load all new plugins and then unload all removed plugins
		"""
		self.__plugin_operation_thread_check()
		self._plugin_manager.refresh_changed_plugins()

	def manipulate_plugins(
			self, *,
			load: Optional[List[PathStr]] = None,    # file paths
			unload: Optional[List[str]] = None,      # plugin ids
			reload: Optional[List[str]] = None,      # plugin ids
			enable: Optional[List[PathStr]] = None,  # file paths
			disable: Optional[List[str]] = None,     # plugin ids
	) -> Optional[bool]:
		"""
		A highly-customizable plugin manipulate API that provides fine-grain control on what to be manipulated:
		load / unload / reload / enable / disable the provided plugins, in a single action

		.. tip::

			Here some different plugin "reload" cases and what actions you should actually provide

			* ``MyPlugin.mcdr`` remains unchanged: reload ``my_plugin``
			* ``MyPlugin.mcdr`` changes its content: reload ``my_plugin``
			* ``MyPlugin.mcdr`` is replaced with an upgraded ``MyPlugin_v2.mcdr``: unload ``my_plugin`` and load ``MyPlugin_v2.mcdr`` in one call

		:param load: An optional plugin **file path** list containing plugins to be loaded
		:param unload: An optional plugin **ID** list containing plugins to be loaded
		:param reload: An optional plugin **ID** list containing plugins to be reloaded
		:param enable: An optional plugin **file path** list containing plugins to be enabled
		:param disable: An optional plugin **ID** list containing plugins to be disabled
		:return: True if all operation succeeded, False if failed, None if it's a not-suggested chained sync plugin operation

		.. versionadded:: v2.13.0
		"""
		def map_to_path(paths: Optional[List[PathStr]]) -> Optional[List[Path]]:
			if paths is not None:
				return list(map(Path, paths))
			else:
				return None

		def map_to_regular(plugin_ids: Optional[List[str]]) -> Optional[List['RegularPlugin']]:
			if plugin_ids is not None:
				plugins = []
				for plugin_id in plugin_ids:
					class_utils.check_type(plugin_id, str)
					plugin = self._plugin_manager.get_regular_plugin_from_id(plugin_id)
					if plugin is not None:
						plugins.append(plugin)
					else:
						self.logger.warning('Skipping not-exist regular plugin with ID {}'.format(plugin_id))
				return plugins
			else:
				return None

		self.__plugin_operation_thread_check()
		future = self._plugin_manager.manipulate_plugins(
			load=map_to_path(load),
			unload=map_to_regular(unload),
			reload=map_to_regular(reload),
			enable=map_to_path(enable),
			disable=map_to_regular(disable),
		)
		if future.done():
			por = future.result()
			return por.load_result.is_success_or_empty() and por.reload_result.is_success_or_empty() and por.unload_result.is_success_or_empty()
		else:
			return False  # chained sync plugin operation

	def dispatch_event(self, event: PluginEvent, args: Tuple[Any, ...], *, on_executor_thread: bool = True) -> None:
		"""
		Dispatch an event to all loaded plugins

		The event will be immediately dispatch if it's on the task executor thread, or gets enqueued if it's on other thread

		.. note:: You cannot dispatch an event with the same event id to any MCDR built-in event

		Example:

			For the event dispatcher plugin::

				server.dispatch_event(LiteralEvent('my_plugin.my_event'), (1, 'a'))

			For the event listener plugin::

				def do_something(server: PluginServerInterface, int_data: int, str_data: str):
					pass

				server.register_event_listener('my_plugin.my_event', do_something)

		:param event: The event to dispatch. It needs to be a :class:`~mcdreforged.plugin.plugin_event.PluginEvent`
			instance. For simple usage, you can create a :class:`~mcdreforged.plugin.plugin_event.LiteralEvent` instance for this argument
		:param args: The argument that will be used to invoke the event listeners. An :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface` instance
			will be automatically added to the beginning of the argument list
		:keyword on_executor_thread: By default the event will be dispatched in a new task in task executor thread
			If it's set to False. The event will be dispatched immediately
		"""
		class_utils.check_type(event, PluginEvent)
		if MCDRPluginEvents.contains_id(event.id):
			raise ValueError('Cannot dispatch event with already exists event id {}'.format(event.id))

		if on_executor_thread:
			dispatch_policy = self._plugin_manager.DispatchEventPolicy.always_new_task
		else:
			dispatch_policy = self._plugin_manager.DispatchEventPolicy.directly_invoke
		self._plugin_manager.dispatch_event(event, args, dispatch_policy=dispatch_policy)

	# ------------------------
	#      Configuration
	# ------------------------

	def get_mcdr_language(self) -> str:
		"""
		Return the current language MCDR is using
		"""
		return self._mcdr_server.translation_manager.language

	def get_mcdr_config(self) -> dict:
		"""
		Return the current config of MCDR as a dict
		"""
		return self._mcdr_server.config.serialize()

	def modify_mcdr_config(self, changes: Dict[Union[Tuple[str], str], Any]):
		"""
		Modify the configuration of MCDR

		The modification will be written to the disk and take effect immediately

		Currently, MCDR will not validate the type of the value

		Example usages::

			server.modify_mcdr_config({'encoding': 'utf8'})
			server.modify_mcdr_config({'rcon.address': '127.0.0.1', 'rcon.port': 23000})
			server.modify_mcdr_config({('debug', 'command'): True})

		:param changes:

			A dict storing the changes to the config. For the entries of the dict:
			The key can be a tuple storing the path to the config value, or a str that concat the path with ``"."``;
			The value is the config value to be set

		.. versionadded:: v2.7.0
		"""
		self._mcdr_server.config_manager.set_values(changes)
		self._mcdr_server.config_manager.save()
		self._mcdr_server.on_config_changed(log=False)

	def reload_config_file(self, *, log: bool = False):
		"""
		Reload the configuration of MCDR from config file

		It has the same effect as command ``!!MCDR reload config``

		:keyword log: If the config changing messages should be logged

		.. versionadded:: v2.7.0
		"""
		self._mcdr_server.load_config(log=log)

	# ------------------------
	#       Permission
	# ------------------------

	def get_permission_level(self, obj: Union[str, Info, CommandSource]) -> int:
		"""
		Return an int indicating permission level number the given object has

		The object could be a str indicating the name of a player,
		an :class:`~mcdreforged.info_reactor.info.Info` instance
		or a :class:`command source <mcdreforged.command.command_source.CommandSource>`

		:param obj: The object you are querying
		:raise TypeError: If the type of the given object is not supported for permission querying
		"""
		if isinstance(obj, Info):  # Info instance
			obj = obj.get_command_source()
			if obj is None:
				raise TypeError('The Info instance is not from a user')
		if isinstance(obj, CommandSource):  # Command Source
			return obj.get_permission_level()
		elif isinstance(obj, str):  # Player name
			return self._mcdr_server.permission_manager.get_player_permission_level(obj)
		else:
			raise TypeError('Unsupported permission level querying for type {}'.format(type(obj)))

	def set_permission_level(self, player: str, value: PermissionParam) -> None:
		"""
		Set the permission level of the given player

		:param player: The name of the player that you want to set his/her permission level
		:param value: The target permission level you want to set the player to. It can be an int or a str as long as
			it's related to the permission level. Available examples: ``1``, ``"1"``, ``"user"``
		:raise TypeError: If the value parameter doesn't properly represent a permission level
		"""
		level = PermissionLevel.get_level(value)
		if level is None:
			raise TypeError('Parameter level needs to be a permission related value')
		self._mcdr_server.permission_manager.set_permission_level(player, level)

	def reload_permission_file(self):
		"""
		Reload the permission of MCDR from permission file

		It has the same effect as command ``!!MCDR reload permission``

		.. versionadded:: v2.7.0
		"""
		self._mcdr_server.permission_manager.load_permission_file()

	# ------------------------
	#         Command
	# ------------------------

	def get_plugin_command_source(self) -> PluginCommandSource:
		"""
		Return a plugin command source, which can be used to execute MCDR commands

		It's not player or console, it has maximum permission level, it uses :attr:`logger` for replying
		"""
		return PluginCommandSource(self, None)

	def get_player_command_source(self, player: str) -> PlayerCommandSource:
		"""
		Return a player command source, which can be used to simulate a player executing MCDR commands

		Note: the :class:`~mcdreforged.info_reactor.info.Info` instance bound to the returned command source
		is a dummy one that contains nothing

		:param player: The name of the player
		"""
		info = Info(InfoSource.SERVER, '')
		command_source = PlayerCommandSource(self._mcdr_server, info, player)
		# noinspection PyProtectedMember
		info._attach_and_finalize(self._mcdr_server, command_source=command_source)
		return command_source

	def get_console_command_source(self) -> ConsoleCommandSource:
		"""
		Return a console command source, which can be used to simulate the console executing MCDR commands

		Note: the :class:`~mcdreforged.info_reactor.info.Info` instance bound to the returned command source
		is a dummy one that contains nothing
		"""
		info = Info(InfoSource.CONSOLE, '')
		command_source = ConsoleCommandSource(self._mcdr_server, info)
		# noinspection PyProtectedMember
		info._attach_and_finalize(self._mcdr_server, command_source=command_source)
		return command_source

	def execute_command(self, command: str, source: CommandSource = None) -> None:
		"""
		Execute a single command in MCDR's command system

		.. seealso::

			:meth:`execute` if you want to send some text to server's standard input stream

		:param command: The command you want to execute
		:param source: The command source that is used to execute the command. If it's not specified MCDR
			will use :meth:`get_plugin_command_source` to get a fallback command source
		"""
		if source is None:
			source = self.get_plugin_command_source()
		class_utils.check_type(command, str)
		class_utils.check_type(source, CommandSource)
		self._mcdr_server.command_manager.execute_command(command, source)

	# ------------------------
	#    	Preference
	# ------------------------

	def get_preference(self, obj: Union[str, PlayerCommandSource, ConsoleCommandSource]) -> PreferenceItem:
		"""
		Get the MCDR preference of the given object

		The object can be a str indicating the name of a player, or a
		command source. For command source, only :class:`~mcdreforged.command.command_source.PlayerCommandSource`
		and :class:`~mcdreforged.command.command_source.ConsoleCommandSource` are supported

		:param obj: The object to query preference
		:raise TypeError: If the type of the given object is not supported for preference querying

		.. versionadded:: v2.1.0
		"""
		return self._mcdr_server.preference_manager.get_preference(obj, strict_type_check=True)

	def get_default_preference(self) -> PreferenceItem:
		"""
		Get the default MCDR preference

		.. versionadded:: v2.8.0
		"""
		return self._mcdr_server.preference_manager.get_default_preference()

	def set_preference(self, obj: Union[str, PlayerCommandSource, ConsoleCommandSource], preference: PreferenceItem):
		"""
		Set the MCDR preference of the given object

		The object can be a str indicating the name of a player, or a
		command source. For command source, only :class:`~mcdreforged.command.command_source.PlayerCommandSource`
		and :class:`~mcdreforged.command.command_source.ConsoleCommandSource` are supported

		:param obj: The object to set preference
		:param preference: The preference to be set
		:raise TypeError: If the type of the given object is not supported for preference querying

		.. versionadded:: v2.8.0
		"""
		return self._mcdr_server.preference_manager.set_preference(obj, preference)

	# ------------------------
	#    	   Misc
	# ------------------------

	def is_on_executor_thread(self) -> bool:
		"""
		Return if the current thread is the task executor thread

		Task executor thread is the main thread to parse messages and trigger listeners where some ServerInterface APIs
		are required to be invoked on
		"""
		return self._mcdr_server.task_executor.is_on_thread()

	def is_on_async_executor_thread(self) -> bool:
		"""
		Return if the current thread is the async task executor thread

		Async task executor thread is where all async event listener callbacks are invoked

		.. versionadded:: v2.14.0
		.. warning:: Beta API
		"""
		return self._mcdr_server.async_task_executor.is_on_thread()

	def get_event_loop(self) -> asyncio.AbstractEventLoop:
		"""
		Return the event loop running in the async executor thread,
		which will be used for all async event listener callbacks

		.. versionadded:: v2.14.0
		.. warning:: Beta API
		"""
		return self._mcdr_server.async_task_executor.get_event_loop()

	def rcon_query(self, command: str) -> Optional[str]:
		"""
		Send command to the server through rcon connection

		:param command: The command you want to send to the rcon server
		:return: The result that server returned from rcon. Return None if rcon is not running or rcon query failed
		"""
		return self._mcdr_server.rcon_manager.send_command(command)

	def schedule_task(
			self, callable_: Union[Callable[[], _T], Coroutine[Any, Any, _T]], *,
			block: bool = False, timeout: Optional[float] = None
	) -> 'Future[_T]':
		"""
		Schedule a callback task to be run in task executor / async task executor thread

		:param callable_: The callable or coroutine object to be run. It should accept 0 parameter
		:keyword block: If blocks until the callable finished execution
		:keyword timeout: The timeout of the blocking operation if ``block=True``

		.. versionadded:: v2.14.0
			The *callback* param now supports :external:func:`coroutine object <inspect.iscoroutine>`
			or :external:func:`coroutine function <inspect.iscoroutinefunction>`

			The return value is now a :external:class:`~concurrent.futures.Future`

		.. warning:: Beta API
		"""
		if inspect.iscoroutine(callable_):
			future = self._mcdr_server.async_task_executor.submit(callable_)
		elif inspect.iscoroutinefunction(callable_):
			future = self._mcdr_server.async_task_executor.submit(callable_())
		elif callable(callable_):
			future = self._mcdr_server.task_executor.submit(callable_)
		else:
			raise TypeError(type(callable_))
		if block:
			future_utils.wait(future, timeout)
		return future
