import functools
import json
import os
import time
from typing import Callable, TYPE_CHECKING, Tuple, Any, Union, Optional, List, IO, Dict, Type, TypeVar

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource, PluginCommandSource
from mcdreforged.constants import plugin_constant
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.mcdr_state import MCDReforgedFlag
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.operation_result import SingleOperationResult, PluginOperationResult
from mcdreforged.plugin.plugin_event import EventListener, LiteralEvent, PluginEvent, MCDRPluginEvents
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY, HelpMessage
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.plugin.type.plugin import AbstractPlugin
from mcdreforged.preference.preference_manager import PreferenceItem
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_util
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.logger import MCDReforgedLogger, DebugOption
from mcdreforged.utils.serializer import Serializable
from mcdreforged.utils.types import MessageText, TranslationKeyDictRich, TranslationKeyDictNested

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.regular_plugin import RegularPlugin


SerializableType = TypeVar('SerializableType')


class ServerInterface:
	"""
	An interface class for plugins to control the server
	"""

	MCDR = True  # Identifier for plugins
	__global_instance: Optional['ServerInterface'] = None  # For singleton instance storage

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self._mcdr_server = mcdr_server
		if type(self) is ServerInterface:
			# singleton, should only occurs during MCDReforgedServer construction
			if ServerInterface.__global_instance is not None:
				self._mcdr_server.logger.warning('Double assigning the singleton instance in {}'.format(self.__class__.__name__), stack_info=True)
			ServerInterface.__global_instance = self

	@functools.lru_cache(maxsize=512, typed=True)
	def __get_logger(self, plugin_id: str):
		return MCDReforgedLogger(self._mcdr_server, plugin_id)

	@property
	def logger(self) -> MCDReforgedLogger:
		"""
		Yes, a nice logger for you to use
		"""
		plugin = self._mcdr_server.plugin_manager.get_current_running_plugin()
		if plugin is not None:
			return self.__get_logger(plugin.get_id())
		else:
			return self._mcdr_server.logger

	# ------------------------
	#          Utils
	# ------------------------

	@classmethod
	def get_instance(cls) -> Optional['ServerInterface']:
		"""
		A class method, for plugins to get a ServerInterface instance anywhere as long as MCDR is running
		"""
		return cls.__global_instance

	def tr(self, translation_key: str, *args, language: Optional[str] = None, **kwargs) -> MessageText:
		"""
		Return a translated text corresponded to the translation key and format the text with given args and kwargs
		If args or kwargs contains RText element, then the result will be a RText, otherwise the result will be a regular str
		If the translation key is not recognized, the return value will be the translation key itself
		:param translation_key: The key of the translation
		:param args: The args to be formatted
		:param language: Specific language to be used in this translation, or the language that MCDR is using will be used
		:param kwargs: The kwargs to be formatted
		"""
		return self._mcdr_server.tr(translation_key, *args, language=language, **kwargs)

	def rtr(self, translation_key: str, *args, **kwargs) -> RTextMCDRTranslation:
		"""
		Return a RText derived component RTextMCDRTranslation, that only translates itself right before displaying or serializing
		Using this method instead of tr() allows you to display your texts in user's preferred language automatically
		Of course you can construct RTextMCDRTranslation yourself instead of using this method if you want
		:param translation_key: The key of the translation
		:param args: The args to be formatted
		:param kwargs: The kwargs to be formatted
		"""
		text = RTextMCDRTranslation(translation_key, *args, **kwargs)
		text.set_translator(self.tr)  # not that necessary tbh, just in case self.tr != ServerInterface.get_instance().tr somehow
		return text

	def as_basic_server_interface(self) -> 'ServerInterface':
		"""
		Return a ServerInterface instance. The type of the return value is exactly the ServerInterface
		It's used for removing the plugin information inside PluginServerInterface when you need to send a ServerInterface
		"""
		return self.get_instance()

	def as_plugin_server_interface(self) -> Optional['PluginServerInterface']:
		"""
		Return a PluginServerInterface instance. If current thread is not a MCDR provided thread and the object is not
		a PluginServerInterface instance, it will return None
		"""
		plugin = self._mcdr_server.plugin_manager.get_current_running_plugin()
		if plugin is not None:
			return plugin.server_interface
		return None

	# ------------------------
	#      Server Control
	# ------------------------

	def start(self) -> bool:
		"""
		Start the server
		:return: If the action succeed it's True. If the server is running or being starting by other plugin return False
		"""
		return self._mcdr_server.start_server()

	def stop(self) -> None:
		"""
		Soft shutting down the server by sending the correct stop command to the server
		MCDR will keep running unless exit() is invoked
		"""
		self._mcdr_server.remove_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
		self._mcdr_server.stop(forced=False)

	def kill(self) -> None:
		"""
		Kill the server process group
		MCDR will keep running unless exit() is invoked
		"""
		self._mcdr_server.stop(forced=True)

	def wait_for_start(self) -> None:
		"""
		Wait until the server is able to start. In other words, wait until the server is stopped
		"""
		while self.is_server_running():
			time.sleep(0.01)

	def restart(self) -> None:
		"""
		Restart the server
		It will first soft stop the server and then wait until the server is stopped, then start the server up
		"""
		if self.is_server_running():
			self.stop()
			self.wait_for_start()
			self.start()

	def stop_exit(self) -> None:
		"""
		Soft stop the server and exit MCDR
		"""
		self._mcdr_server.stop(forced=False)

	def exit(self) -> None:
		"""
		Exit MCDR when the server is stopped
		Basically it's the same to invoking set_exit_after_stop_flag(True), but with an extra server not running check
		:raise: IllegalCallError, if the server is not stopped
		"""
		if self._mcdr_server.is_server_running():
			raise IllegalCallError('Cannot exit MCDR when the server is running')
		self._mcdr_server.with_flag(MCDReforgedFlag.EXIT_AFTER_STOP)

	def set_exit_after_stop_flag(self, flag_value: bool) -> None:
		"""
		Set the flag that indicating if MCDR should exit when the server has stopped
		If set to true, after the server stops MCDR will exit,
		otherwise MCDR will just keep running
		"""
		if flag_value:
			self._mcdr_server.with_flag(MCDReforgedFlag.EXIT_AFTER_STOP)
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
		if self._mcdr_server.process is not None:
			return self._mcdr_server.process.pid
		return None

	def get_server_information(self) -> ServerInformation:
		"""
		Return a ServerInformation object indicating the information of the current server, interred from the output of the server
		Field(s) might be None if the server is offline, or the related information has not been parsed
		:return: a ServerInformation object
		"""
		return self._mcdr_server.server_information.copy()

	# ------------------------
	#     Text Interaction
	# ------------------------

	def execute(self, text: str, *, encoding: Optional[str] = None) -> None:
		"""
		Execute a command by sending the command content to server's standard input stream
		:param str text: The content of the command you want to send
		:param str encoding: The encoding method for the text
		"""
		self.logger.debug('Sending command "{}"'.format(text), option=DebugOption.PLUGIN)
		self._mcdr_server.send(text, encoding=encoding)

	@property
	def __server_handler(self) -> 'AbstractServerHandler':
		return self._mcdr_server.server_handler_manager.get_current_handler()

	def tell(self, player: str, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Use command like /tellraw to send the message to the specific player
		:param player: The name of the player you want to tell
		:param text: the message you want to send to the player
		:param encoding: The encoding method for the text
		"""
		with RTextMCDRTranslation.language_context(self._mcdr_server.preference_manager.get_preferred_language(player)):
			command = self.__server_handler.get_send_message_command(player, text, self.get_server_information())
		if command is not None:
			self.execute(command, encoding=encoding)

	def say(self, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Use command like /tellraw @a to broadcast the message in game
		:param text: the message you want to send
		:param encoding: The encoding method for the text
		"""
		command = self.__server_handler.get_broadcast_message_command(text, self.get_server_information())
		if command is not None:
			self.execute(command, encoding=encoding)

	def broadcast(self, text: MessageText, *, encoding: Optional[str] = None) -> None:
		"""
		Broadcast the message in game and to the console
		:param text: the message you want to send
		:param encoding: The encoding method for the text
		"""
		self.say(text, encoding=encoding)
		misc_util.print_text_to_console(self.logger, text)

	def reply(self, info: Info, text: MessageText, *, encoding: Optional[str] = None, console_text: Optional[MessageText] = None):
		"""
		Reply to the source of the Info
		If the Info is from a player then use tell to reply the player
		Otherwise if the Info is from the console use logger.info to output to the console
		In the rest of the situations, the Info is not from a user, a IllegalCallError is raised
		:param info: the Info you want to reply to
		:param text: the message you want to send
		:param console_text: If it's specified, console_text will be used instead of text when replying to console
		:param encoding: The encoding method for the text
		"""
		source = info.get_command_source()
		if source is None:
			raise IllegalCallError('Cannot reply to the given info instance')
		if not source.is_console:
			if console_text is not None:
				text = console_text
		source.reply(text, encoding=encoding)

	# ------------------------
	#      Plugin Queries
	# ------------------------

	def __existed_plugin_info_getter(self, plugin_id: str, handler: Callable[['AbstractPlugin'], Any], *, regular: bool):
		if regular:
			plugin = self._mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		else:
			plugin = self._mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
		if plugin is not None:
			return handler(plugin)
		return None

	def get_plugin_metadata(self, plugin_id: str) -> Optional[Metadata]:
		"""
		Return the metadata of the specified plugin, or None if the plugin doesn't exist
		:param plugin_id: The plugin id of the plugin to query metadata
		"""
		return self.__existed_plugin_info_getter(plugin_id, lambda plugin: plugin.get_metadata(), regular=False)

	def get_plugin_file_path(self, plugin_id: str) -> Optional[str]:
		"""
		Return the file path of the specified plugin, or None if the plugin doesn't exist
		:param plugin_id: The plugin id of the plugin to query file path
		"""
		return self.__existed_plugin_info_getter(plugin_id, lambda plugin: plugin.plugin_path, regular=False)

	def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
		"""
		Return the entrypoint module instance of the specific plugin, or None if the plugin doesn't exist
		:param plugin_id: The plugin id of the plugin you want
		:return: A entrypoint module instance, or None if the plugin doesn't exist
		"""
		return self.__existed_plugin_info_getter(plugin_id, lambda plugin: plugin.entry_module_instance, regular=True)

	def get_plugin_list(self) -> List[str]:
		"""
		Return a list containing all loaded plugin id like ["my_plugin", "another_plugin"]
		"""
		return [plugin.get_id() for plugin in self._mcdr_server.plugin_manager.get_regular_plugins()]

	def get_all_metadata(self) -> Dict[str, Metadata]:
		"""
		Return a dict containing metadatas of all loaded plugin with (plugin_id, metadata) as key-value pair
		"""
		result = {}
		for plugin in self._mcdr_server.plugin_manager.get_all_plugins():
			result[plugin.get_id()] = plugin.get_metadata()
		return result

	# ------------------------
	#     Plugin Operations
	# ------------------------

	# Notes: All plugin manipulation will trigger a dependency check, which might cause unwanted plugin operations

	def __check_if_success(self, operation_result: SingleOperationResult, check_loaded: bool) -> bool:
		"""
		Check if there's any plugin inside the given operation result (load result / reload result etc.)
		Then check if the plugin passed the dependency check if param check_loaded is True
		"""
		success = operation_result.has_success()
		if success and check_loaded:
			plugin = operation_result.success_list[0]
			success = plugin in self._mcdr_server.plugin_manager.last_operation_result.dependency_check_result.success_list
		return success

	def __not_loaded_regular_plugin_manipulate(self, plugin_file_path: str, handler: Callable[['PluginManager'], Callable[[str], Any]]) -> bool:
		"""
		Manipulate a not loaded regular plugin from a given file path
		:param plugin_file_path: The path to the not loaded new plugin
		:param handler: What you want to do with Plugin Manager to the given file path
		:return: If success
		"""
		self._mcdr_server.plugin_manager.last_operation_result.clear()
		handler(self._mcdr_server.plugin_manager)(plugin_file_path)
		return self.__check_if_success(self._mcdr_server.plugin_manager.last_operation_result.load_result, check_loaded=True)  # the operations is always loading a plugin

	def __existed_regular_plugin_manipulate(self, plugin_id: str, handler: Callable[['PluginManager'], Callable[['RegularPlugin'], Any]], result_getter: Callable[[PluginOperationResult], SingleOperationResult], check_loaded: bool) -> bool or None:
		"""
		Manipulate a loaded regular plugin from a given plugin id
		:param plugin_id: The plugin id of the plugin you want to manipulate
		:param handler: What callable you want to use with Plugin Manager to the plugin id,
		the returned callable accepts the plugin instance
		:param result_getter: How to get the single operation result from the plugin operation result.
		It's used to determine if the operation succeeded
		:return: If success, None if plugin not found
		"""
		plugin = self._mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			self._mcdr_server.plugin_manager.last_operation_result.clear()
			handler(self._mcdr_server.plugin_manager)(plugin)
			opt_result = result_getter(self._mcdr_server.plugin_manager.last_operation_result)
			return self.__check_if_success(opt_result, check_loaded)
		return None

	def load_plugin(self, plugin_file_path: str) -> bool:
		"""
		Load a plugin from the given file path
		:param plugin_file_path: The file path of the plugin to load. Example: "plugins/my_plugin.py"
		:return: If the plugin gets loaded successfully
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.load_plugin)

	def enable_plugin(self, plugin_file_path: str) -> bool:
		"""
		Enable an unloaded plugin from the given path
		:param plugin_file_path: The file path of the plugin to enable. Example: "plugins/my_plugin.py.disabled"
		:return: If the plugin gets enabled successfully
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.enable_plugin)

	def reload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Reload a plugin specified by plugin id
		:param plugin_id: The id of the plugin to reload. Example: "my_plugin"
		:return: A bool indicating if the plugin gets reloaded successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.reload_plugin, lambda lor: lor.reload_result, check_loaded=True)

	def unload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Unload a plugin specified by plugin id
		:param plugin_id: The id of the plugin to unload. Example: "my_plugin"
		:return: A bool indicating if the plugin gets unloaded successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.unload_plugin, lambda lor: lor.unload_result, check_loaded=False)

	def disable_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Disable an unloaded plugin from the given path
		:param plugin_id: The id of the plugin to disable. Example: "my_plugin"
		:return: A bool indicating if the plugin gets disabled successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.disable_plugin, lambda lor: lor.unload_result, check_loaded=False)

	def refresh_all_plugins(self) -> None:
		"""
		Reload all plugins, load all new plugins and then unload all removed plugins
		"""
		self._mcdr_server.plugin_manager.refresh_all_plugins()

	def refresh_changed_plugins(self) -> None:
		"""
		Reload all changed plugins, load all new plugins and then unload all removed plugins
		"""
		self._mcdr_server.plugin_manager.refresh_changed_plugins()

	def dispatch_event(self, event: PluginEvent, args: Tuple[Any, ...], *, on_executor_thread: bool = True) -> None:
		"""
		Dispatch an event to all loaded plugins
		The event will be immediately dispatch if it's on the task executor thread, or gets enqueued if it's on other thread
		:param event: The event to dispatch. It need to be a PluginEvent instance. For simple usage, you can create a
		LiteralEvent instance for this argument
		:param args: The argument that will be used to invoke the event listeners. An ServerInterface instance will be
		automatically added to the beginning of the argument list
		:param on_executor_thread: By default the event will be dispatched in a new task in task executor thread
		If it's set to false. The event will be dispatched immediately
		"""
		misc_util.check_type(event, PluginEvent)
		if MCDRPluginEvents.contains_id(event.id):
			raise ValueError('Cannot dispatch event with already exists event id {}'.format(event.id))
		self._mcdr_server.plugin_manager.dispatch_event(event, args, on_executor_thread=on_executor_thread)

	# ------------------------
	#        Permission
	# ------------------------

	def get_permission_level(self, obj: Union[str, Info, CommandSource]) -> int:
		"""
		Return an int indicating permission level number the given object has
		The object could be a str indicating the name of a player, an Info instance or a command source
		:param obj: The object your are querying
		:raise: TypeError, if the type of the given object is not supported for permission querying
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

	def set_permission_level(self, player: str, value: Union[int, str]) -> None:
		"""
		Set the permission level of the given player
		:param player: The name of the player that you want to set his/her permission level
		:param value: The target permission level you want to set the player to. It can be an int or a str as long as
		it's related to the permission level. Available examples: 1, '1', 'user'
		:raise: TypeError if the value parameter doesn't proper represent a permission level
		"""
		level = PermissionLevel.get_level(value)
		if level is None:
			raise TypeError('Parameter level needs to be a permission related value')
		self._mcdr_server.permission_manager.set_permission_level(player, value)

	# ------------------------
	#         Command
	# ------------------------

	def get_plugin_command_source(self) -> PluginCommandSource:
		"""
		Return a simple plugin command source for e.g. command execution
		It's not player or console, it has maximum permission level, it use ServerInterface.logger for replying
		"""
		return PluginCommandSource(self, None)

	def execute_command(self, command: str, source: CommandSource = None) -> None:
		"""
		Execute a single command using the command system of MCDR
		:param str command: The command you want to execute
		:param CommandSource source: The command source that is used to execute the command. If it's not specified MCDR
		will use ServerInterface.get_plugin_command_source as fallback command source
		"""
		if source is None:
			source = self.get_plugin_command_source()
		misc_util.check_type(command, str)
		misc_util.check_type(source, CommandSource)
		self._mcdr_server.command_manager.execute_command(command, source)

	# ------------------------
	#        Preference
	# ------------------------

	def get_preference(self, obj: Union[str, CommandSource]) -> PreferenceItem:
		"""
		Return the MCDR preference of the given object. The object can be a str indicating the name of a player, or a
		command source. For command source, only PlayerCommandSource and ConsoleCommandSource are supported
		:param obj: The object to querying preference
		:raise: TypeError, if the type of the given object is not supported for preference querying
		"""
		pref = self._mcdr_server.preference_manager.get_preference(obj, strict_type_check=True)
		return PreferenceItem.deserialize(pref.serialize())  # make a copy

	# ------------------------
	#           Misc
	# ------------------------

	def is_on_executor_thread(self) -> bool:
		"""
		Return if the current thread is the task executor thread
		Task executor thread is the main thread to parse messages and trigger listeners where some ServerInterface APIs
		are required to be invoked on
		"""
		return self._mcdr_server.task_executor.is_on_thread()

	def rcon_query(self, command: str) -> Optional[str]:
		"""
		Send command to the server through rcon connection
		:param str command: The command you want to send to the rcon server
		:return: The result that server returned from rcon. Return None if rcon is not running or rcon query failed
		"""
		return self._mcdr_server.rcon_manager.send_command(command)

	def get_mcdr_language(self) -> str:
		"""
		Return the current language MCDR is using
		"""
		return self._mcdr_server.translation_manager.language

	def get_mcdr_config(self) -> dict:
		"""
		Return the current config of MCDR as a dict
		"""
		return self._mcdr_server.config.to_dict()

	def schedule_task(self, callable_: Callable[[], Any], *, block: bool = False, timeout: Optional[float] = None) -> None:
		"""
		Schedule a callback task to be run in task executor thread
		:param callable_: The callable object to be run. It should accept 0 parameter
		:param block: If blocks until the callable finished execution
		:param timeout: The timeout of the blocking operation if block=True
		"""
		self._mcdr_server.task_executor.add_regular_task(callable_, block=block, timeout=timeout)


class PluginServerInterface(ServerInterface):
	"""
	An extended ServerInterface class that adds the ability for plugins to control the plugin itself
	"""

	def __init__(self, mcdr_server: 'MCDReforgedServer', plugin: AbstractPlugin):
		super().__init__(mcdr_server)
		self.__plugin = plugin
		self.__logger_for_plugin = None  # type: Optional[MCDReforgedLogger]

	@property
	def logger(self) -> MCDReforgedLogger:
		if self.__logger_for_plugin is None:
			try:
				self.__logger_for_plugin = MCDReforgedLogger(self._mcdr_server, self.__plugin.get_id())
			except:
				return super().logger
		return self.__logger_for_plugin

	def as_plugin_server_interface(self) -> Optional['PluginServerInterface']:
		return self

	# -----------------------
	#   Overwritten methods
	# -----------------------

	def get_plugin_command_source(self) -> PluginCommandSource:
		return PluginCommandSource(self, self.__plugin)

	# ------------------------
	#     Plugin Registry
	# ------------------------

	def register_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: Optional[int] = None) -> None:
		"""
		Register an event listener for the current plugin
		:param event: The id of the event, or a PluginEvent instance. It indicates the target event for the plugin to listen
		:param callback: The callback listener method for the event
		:param priority: The priority of the listener. It will be set to the default value 1000 if it's not specified
		"""
		if priority is None:
			priority = DEFAULT_LISTENER_PRIORITY
		if isinstance(event, str):
			event = LiteralEvent(event_id=event)
		self.__plugin.register_event_listener(event, EventListener(self.__plugin, callback, priority))

	def register_command(self, root_node: Literal) -> None:
		"""
		Register an event listener for the current plugin
		:param root_node: the root node of your command tree. It should be a Literal node
		"""
		self.__plugin.register_command(root_node)

	def register_help_message(self, prefix: str, message: Union[MessageText, TranslationKeyDictRich], permission: int = PermissionLevel.MINIMUM_LEVEL) -> None:
		"""
		Register a help message for the current plugin, which is used in !!help command
		:param prefix: The help command of your plugin. When player click on the displayed message it will suggest this
		prefix parameter to the player. It's recommend to set it to the entry command of your plugin
		:param message: A neat command description. It can be a str or a RText. Also it can be a dict maps from language to description message
		:param permission: The minimum permission level for the user to see this help message. With default, anyone
		can see this message
		"""
		self.__plugin.register_help_message(HelpMessage(self.__plugin, prefix, message, permission))

	def register_translation(self, language: str, mapping: TranslationKeyDictNested) -> None:
		"""
		Register a translation mapping for a specific language for the current plugin
		:param language: The language of this translation
		:param mapping: A dict which maps translation keys into translated text. The translation key could be expressed as node name which under root node or the path of a nested multi-level nodes
		"""
		self.__plugin.register_translation(language, mapping)

	# ------------------------
	#      Plugin Utils
	# ------------------------

	def get_self_metadata(self) -> Metadata:
		"""
		Return the metadata of the plugin itself
		"""
		return self.__plugin.get_metadata()

	def get_data_folder(self) -> str:
		"""
		Return a unified data directory path for the current plugin
		The path of the folder will be "config/plugin_id/" where "plugin_id" is the id of the current plugin
		If the directory does not exist, create it
		:return: The path to the data directory
		"""
		plugin_data_folder = os.path.join(plugin_constant.PLUGIN_CONFIG_DIRECTORY, self.__plugin.get_id())
		if not os.path.isdir(plugin_data_folder):
			os.makedirs(plugin_data_folder)
		return plugin_data_folder

	def open_bundled_file(self, related_file_path: str) -> IO[bytes]:
		"""
		Open a file inside the plugin with readonly binary mode
		:param related_file_path: The related file path in your plugin to the file you want to open
		:return: A un-decoded bytes file-like object
		:raise: FileNotFoundError if the plugin is not a packed plugin (that is, a solo plugin)
		"""
		if not isinstance(self.__plugin, MultiFilePlugin):
			raise FileNotFoundError('Only packed plugin supported this API, found plugin type: {}'.format(self.__plugin.__class__))
		return self.__plugin.open_file(related_file_path)

	def load_config_simple(
			self, file_name: str = 'config.json', default_config: Optional = None, *,
			in_data_folder: bool = True, echo_in_console: bool = True, source_to_reply: Optional[CommandSource] = None,
			target_class: Optional[Type[SerializableType]] = None, encoding: str = 'utf8'
		) -> Union[dict, SerializableType]:
		"""
		A simple method to load a dict or Serializable type config from a json file
		Default config is supported. Missing key-values in the loaded config object will be filled using the default config
		:param file_name: The name of the config file. It can also be a path to the config file
		:param default_config: A dict contains the default config. It's required when the config file is missing,
		or exception will be risen. If target_class is given and default_config is missing, the default values in target_class
		will be used when the config file is missing
		:param in_data_folder: If True, the parent directory of file operating is the data folder of the plugin
		:param echo_in_console: If logging messages in console about config loading
		:param source_to_reply: The command source for replying logging messages
		:param target_class: A class derived from Serializable. When specified the loaded config data will be deserialized
		to a instance of target_class which will be returned as return value
		:param encoding: The encoding method to read the config file
		:return: A dict contains the loaded and processed config
		"""
		def log(msg):
			if isinstance(source_to_reply, CommandSource):
				source_to_reply.reply(msg)
			if echo_in_console:
				self.logger.info(msg)

		if target_class is not None:
			misc_util.check_class(target_class, Serializable)
			target_class: Serializable
			if default_config is None:
				default_config = target_class.get_default().serialize()
		config_file_path = os.path.join(self.get_data_folder(), file_name) if in_data_folder else file_name
		needs_save = False
		try:
			with open(config_file_path, encoding=encoding) as file_handler:
				read_data: dict = json.load(file_handler)
		except Exception as e:
			if default_config is not None:  # use default config
				result_config = default_config.copy()
			else:  # no default config and cannot read config file, raise the error
				raise
			needs_save = True
			log(self._mcdr_server.tr('server_interface.load_config_simple.failed', e))
		else:
			result_config = read_data
			if default_config is not None:
				# constructing the result config based on the given default config
				for key, value in default_config.items():
					if key in read_data:
						result_config[key] = read_data[key]
					else:
						result_config[key] = value
						log(self._mcdr_server.tr('server_interface.load_config_simple.key_missed', key, value))
						needs_save = True
			log(self._mcdr_server.tr('server_interface.load_config_simple.succeed'))
		if target_class is not None:
			try:
				result_config = target_class.deserialize(result_config)
			except Exception as e:
				result_config = target_class.get_default()
				needs_save = True
				log(self._mcdr_server.tr('server_interface.load_config_simple.failed', e))
		else:
			# remove unexpected keys
			if default_config is not None:
				for key in list(result_config.keys()):
					if key not in default_config:
						result_config.pop(key)
		if needs_save:
			self.save_config_simple(result_config, file_name=file_name, in_data_folder=in_data_folder)
		return result_config

	def save_config_simple(
			self, config: Union[dict, Serializable], file_name: str = 'config.json', *,
			in_data_folder: bool = True, encoding: str = 'utf8'
	) -> None:
		"""
		A simple method to save your dict or Serializable type config as a json file
		:param config: The config instance to be saved
		:param file_name: The name of the config file. It can also be a path to the config file
		:param in_data_folder: If True, the parent directory of file operating is the data folder of the plugin
		:param encoding: The encoding method to write the config file
		"""
		config_file_path = os.path.join(self.get_data_folder(), file_name) if in_data_folder else file_name
		if isinstance(config, Serializable):
			data = config.serialize()
		else:
			data = config
		target_folder = os.path.dirname(config_file_path)
		if len(target_folder) > 0 and not os.path.isdir(target_folder):
			os.makedirs(target_folder)
		with open(config_file_path, 'w', encoding=encoding) as file:
			# config file should be nicely readable, so here come the indent and non-ascii chars
			json.dump(data, file, indent=4, ensure_ascii=False)
