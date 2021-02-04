"""
An interface class for plugins to control the server
"""
import functools
import time
from typing import Callable, TYPE_CHECKING, Tuple, Any, Union, Optional, List

from mcdreforged.command.builder.command_node import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.info import Info
from mcdreforged.mcdr_state import ServerState
from mcdreforged.minecraft.rtext import RTextBase, RText
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.operation_result import SingleOperationResult, PluginOperationResult
from mcdreforged.plugin.plugin_event import EventListener, LiteralEvent, PluginEvent, MCDRPluginEvents
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY, HelpMessage
from mcdreforged.utils import misc_util
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.logger import MCDReforgedLogger, DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.plugin import RegularPlugin


def log_call(func):
	"""
	Log plugin call
	Use kwarg is_plugin_call to determined if do log
	"""
	def wrap(self: 'ServerInterface', *args, is_plugin_call=True, **kwargs):
		if is_plugin_call and MCDReforgedLogger.should_log_debug(option=DebugOption.PLUGIN):
			self.logger.debug('Plugin called {}(), args amount: {}'.format(func.__name__, len(args)), no_check=True)
			for arg in args:
				self.logger.debug('  - type: {}, content: {}'.format(type(arg).__name__, arg), no_check=True)
		return func(self, *args, **kwargs)
	return wrap


class ServerInterface:
	MCDR = True  # Identifier for plugins

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.__mcdr_server = mcdr_server
		self.__logger = mcdr_server.logger

	@functools.lru_cache(maxsize=512, typed=True)
	def __get_logger(self, plugin_id: str):
		return MCDReforgedLogger(self.__mcdr_server, plugin_id)

	@property
	def logger(self) -> MCDReforgedLogger:
		try:
			plugin = self.__get_current_plugin()
			plugin_id = plugin.get_metadata().id
		except IllegalCallError:
			return self.__logger
		else:
			return self.__get_logger(plugin_id)

	def __get_current_plugin(self) -> 'RegularPlugin':
		plugin = self.__mcdr_server.plugin_manager.get_current_running_plugin()
		if plugin is not None and plugin.is_regular():
			return plugin
		else:
			raise IllegalCallError('MCDR provided thead is required')

	# ------------------------
	#      Server Control
	# ------------------------

	@log_call
	def start(self) -> bool:
		"""
		Start the server
		:return: If the action succeed it's True. If the server is running or being starting by other plugin return False
		"""
		return self.__mcdr_server.start_server()

	@log_call
	def stop(self) -> None:
		"""
		Soft shutting down the server by sending the correct stop command to the server
		"""
		self.__mcdr_server.set_exit_naturally(False)
		self.__mcdr_server.stop(forced=False)

	@log_call
	def wait_for_start(self) -> None:
		"""
		Wait until the server is able to start. In other words, wait until the server is stopped
		"""
		while self.is_server_running(is_plugin_call=False):
			time.sleep(0.01)

	@log_call
	def restart(self) -> None:
		"""
		Restart the server
		It will first soft stop the server and then wait until the server is stopped, then start the server up
		"""
		if self.is_server_running():
			self.stop(is_plugin_call=False)
			self.wait_for_start(is_plugin_call=False)
			self.start(is_plugin_call=False)

	@log_call
	def stop_exit(self) -> None:
		"""
		Soft stop the server and exit MCDR
		"""
		self.__mcdr_server.stop(forced=False)

	@log_call
	def exit(self) -> None:
		"""
		Exit MCDR when the server is stopped
		:raise: IllegalCallError, if the server is not stopped
		"""
		if self.__mcdr_server.is_server_running():
			raise IllegalCallError('Cannot exit MCDR when the server is running')
		self.__mcdr_server.set_server_state(ServerState.STOPPED)

	@log_call
	def is_server_running(self) -> bool:
		"""
		Return if the server is running
		"""
		return self.__mcdr_server.is_server_running()

	@log_call
	def is_server_startup(self) -> bool:
		"""
		Return if the server has started up
		"""
		return self.__mcdr_server.is_server_startup()

	@log_call
	def is_rcon_running(self) -> bool:
		"""
		Return if MCDR's rcon is running
		"""
		return self.__mcdr_server.rcon_manager.is_running()

	@log_call
	def get_server_pid(self) -> Optional[int]:
		"""
		Return the pid of the server process
		Notes the process with this pid is a bash process, which is the parent process of real server process
		you might be interested in
		:return: The pid of the server. None if the server is stopped
		"""
		if self.__mcdr_server.process is not None:
			return self.__mcdr_server.process.pid
		return None

	# ------------------------
	#     Text Interaction
	# ------------------------

	@log_call
	def execute(self, text: str, *, encoding: Optional[str] = None) -> None:
		"""
		Execute a command by sending the command content to server's standard input stream
		:param str text: The content of the command you want to send
		:param str encoding: The encoding method for the text
		"""
		self.__mcdr_server.send(text, encoding=encoding)

	@log_call
	def tell(self, player: str, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None:
		"""
		Use command like /tellraw to send the message to the specific player
		:param player: The name of the player you want to tell
		:param text: the message you want to send to the player
		:param encoding: The encoding method for the text
		"""
		command = self.__mcdr_server.server_handler_manager.get_current_handler().get_send_message_command(player, text)
		if command is not None:
			self.execute(command, encoding=encoding, is_plugin_call=False)

	@log_call
	def say(self, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None:
		"""
		Use command like /tellraw @a to broadcast the message in game
		:param text: the message you want to send
		:param encoding: The encoding method for the text
		"""
		command = self.__mcdr_server.server_handler_manager.get_current_handler().get_broadcast_message_command(text)
		if command is not None:
			self.execute(command, encoding=encoding, is_plugin_call=False)

	@log_call
	def broadcast(self, text: Union[str, RTextBase], *, encoding: Optional[str] = None) -> None:
		"""
		Broadcast the message in game and to the console
		:param text: the message you want to send
		:param encoding: The encoding method for the text
		"""
		self.say(text, encoding=encoding, is_plugin_call=False)
		misc_util.print_text_to_console(self.logger, text)

	@log_call
	def reply(self, info: Info, text: Union[str, RTextBase], *, encoding: Optional[str] = None, console_text: Optional[Union[str, RTextBase]] = None):
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
			success = plugin in self.__mcdr_server.plugin_manager.last_operation_result.dependency_check_result.success_list
		return success

	def __not_loaded_regular_plugin_manipulate(self, plugin_file_path: str, handler: Callable[['PluginManager'], Callable[[str], Any]]) -> bool:
		"""
		Manipulate a not loaded regular plugin from a given file path
		:param plugin_file_path: The path to the not loaded new plugin
		:param handler: What you want to do with Plugin Manager to the given file path
		:return: If success
		"""
		handler(self.__mcdr_server.plugin_manager)(plugin_file_path)
		return self.__check_if_success(self.__mcdr_server.plugin_manager.last_operation_result.load_result, check_loaded=True)  # the operations is always loading a plugin

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
		plugin = self.__mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			handler(self.__mcdr_server.plugin_manager)(plugin)
			opt_result = result_getter(self.__mcdr_server.plugin_manager.last_operation_result)
			return self.__check_if_success(opt_result, check_loaded)
		return None

	@log_call
	def load_plugin(self, plugin_file_path: str) -> bool:
		"""
		Load a plugin from the given file path
		:param plugin_file_path: The file path of the plugin to load. Example: "plugins/my_plugin.py"
		:return: If the plugin gets loaded successfully
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.load_plugin)

	@log_call
	def enable_plugin(self, plugin_file_path: str) -> bool:
		"""
		Enable an unloaded plugin from the given path
		:param plugin_file_path: The file path of the plugin to enable. Example: "plugins/my_plugin.py.disabled"
		:return: If the plugin gets enabled successfully
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.enable_plugin)

	@log_call
	def reload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Reload a plugin specified by plugin id
		:param plugin_id: The id of the plugin to reload. Example: "my_plugin"
		:return: A bool indicating if the plugin gets reloaded successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.reload_plugin, lambda lor: lor.reload_result, check_loaded=True)

	@log_call
	def unload_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Unload a plugin specified by plugin id
		:param plugin_id: The id of the plugin to unload. Example: "my_plugin"
		:return: A bool indicating if the plugin gets unloaded successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.unload_plugin, lambda lor: lor.unload_result, check_loaded=False)

	@log_call
	def disable_plugin(self, plugin_id: str) -> Optional[bool]:
		"""
		Disable an unloaded plugin from the given path
		:param plugin_id: The id of the plugin to disable. Example: "my_plugin"
		:return: A bool indicating if the plugin gets disabled successfully, or None if plugin not found
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.disable_plugin, lambda lor: lor.unload_result, check_loaded=False)

	@log_call
	def refresh_all_plugins(self) -> None:
		"""
		Reload all plugins, load all new plugins and then unload all removed plugins
		"""
		self.__mcdr_server.plugin_manager.refresh_all_plugins()

	@log_call
	def refresh_changed_plugins(self) -> None:
		"""
		Reload all changed plugins, load all new plugins and then unload all removed plugins
		"""
		self.__mcdr_server.plugin_manager.refresh_changed_plugins()

	@log_call
	def get_plugin_list(self) -> List[str]:
		"""
		Return a list containing all loaded plugin id like ["my_plugin", "another_plugin"]
		"""
		return [plugin.get_id() for plugin in self.__mcdr_server.plugin_manager.get_regular_plugins()]

	def __existed_regular_plugin_info_getter(self, plugin_id: str, handler: Callable[['RegularPlugin'], Any]):
		plugin = self.__mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			return handler(plugin)
		return None

	@log_call
	def get_plugin_metadata(self, plugin_id: str) -> Optional[Metadata]:
		"""
		Return the metadata of the specified plugin, or None if the plugin doesn't exist
		:param plugin_id: The plugin id of the plugin to query metadata
		"""
		return self.__existed_regular_plugin_info_getter(plugin_id, lambda plugin: plugin.get_metadata())

	@log_call
	def get_plugin_file_path(self, plugin_id: str) -> Optional[str]:
		"""
		Return the file path of the specified plugin, or None if the plugin doesn't exist
		:param plugin_id: The plugin id of the plugin to query file path
		"""
		return self.__existed_regular_plugin_info_getter(plugin_id, lambda plugin: plugin.file_path)

	@log_call
	def get_plugin_instance(self, plugin_id: str) -> Optional[Any]:
		"""
		Return the current loaded plugin instance. With this api your plugin can access the same plugin instance to MCDR
		It's quite important to use this instead of manually import the plugin you want if the target plugin needs to
		react to events from MCDR
		:param plugin_id: The plugin id of the plugin you want
		:return: A current loaded plugin instance, or None if the plugin doesn't exist
		"""
		plugin = self.__mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			plugin = plugin.module_instance
		return plugin

	# ------------------------
	#     Plugin Registry
	# ------------------------

	@log_call
	def register_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: int = DEFAULT_LISTENER_PRIORITY) -> None:
		"""
		Register an event listener for the current plugin
		:param event: The id of the event, or a PluginEvent instance. It indicates the target event for the plugin to listen
		:param callback: The callback listener method for the event
		:param priority: The priority of the listener. It will be set to the default value 1000 if it's not specified
		:raise: IllegalCallError if it's not invoked in the task executor thread
		"""
		plugin = self.__get_current_plugin()
		if isinstance(event, str):
			event = LiteralEvent(event_id=event)
		plugin.register_event_listener(event, EventListener(plugin, callback, priority))

	@log_call
	def register_command(self, root_node: Literal) -> None:
		"""
		Register an event listener for the current plugin
		:param root_node: the root node of your command tree. It should be a Literal node
		:raise: IllegalCallError if it's not invoked in the task executor thread
		"""
		plugin = self.__get_current_plugin()
		plugin.register_command(root_node)

	@log_call
	def register_help_message(self, prefix: str, message: Union[str, RTextBase], permission: int = PermissionLevel.MINIMUM_LEVEL) -> None:
		"""
		Register a help message for the current plugin, which is used in !!help command
		:param prefix: The help command of your plugin. When player click on the displayed message it will suggest this
		prefix parameter to the player. It's recommend to set it to the entry command of your plugin
		:param message: A neat command description
		:param permission: The minimum permission level for the user to see this help message. With default, anyone
		can see this message
		:raise: IllegalCallError if it's not invoked in the task executor thread
		"""
		plugin = self.__get_current_plugin()
		if isinstance(message, str):
			message = RText(message)
		plugin.register_help_message(HelpMessage(plugin, prefix, message, permission))

	@log_call
	def dispatch_event(self, event: PluginEvent, args: Tuple[Any, ...], *, on_executor_thread: bool = True) -> None:
		"""
		Dispatch an event to all loaded plugins
		The event will be immediately dispatch if it's on the task executor thread, or gets enqueued if it's on other thread
		:param event: The event to dispatch. It need to be a PluginEvent instance. For simple usage, you can create a
		LiteralEvent instance for this argument
		:param args: The argument that will be used to invoke the event listeners. An ServerInterface instance will be
		automatically added to the beginning of the argument list
		:param on_executor_thread: If it's set to false. The event will be dispatched immediately no matter what the
		current thread is
		"""
		if not isinstance(event, PluginEvent):
			raise TypeError('Excepted {} but {} found'.format(PluginEvent, type(event)))
		if MCDRPluginEvents.contains_id(event.id):
			raise ValueError('Cannot dispatch event with already exists event id {}'.format(event.id))
		self.__mcdr_server.plugin_manager.dispatch_event(event, args, on_executor_thread=on_executor_thread)

	# ------------------------
	#        Permission
	# ------------------------

	@log_call
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
			return self.__mcdr_server.permission_manager.get_player_permission_level(obj)
		else:
			raise TypeError('Unsupported permission level querying for type {}'.format(type(obj)))

	@log_call
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
		self.__mcdr_server.permission_manager.set_permission_level(player, value)

	# ------------------------
	#           Misc
	# ------------------------

	@log_call
	def is_on_executor_thread(self) -> bool:
		"""
		Return if the current thread is the task executor thread
		Task executor thread is the main thread to parse messages and trigger listeners where some ServerInterface APIs
		are required to be invoked on
		"""
		return self.__mcdr_server.task_executor.is_on_thread()

	@log_call
	def rcon_query(self, command: str) -> Optional[str]:
		"""
		Send command to the server through rcon connection
		:param str command: The command you want to send to the rcon server
		:return: The result that server returned from rcon. Return None if rcon is not running or rcon query failed
		"""
		return self.__mcdr_server.rcon_manager.send_command(command)
