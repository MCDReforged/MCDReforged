"""
An interface class for plugins to control the server
"""
import json
import time
from typing import Callable, TYPE_CHECKING, Tuple, Any, Union

from mcdreforged.command.builder.command_node import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.exception import IllegalCallError
from mcdreforged.info import Info
from mcdreforged.logger import MCDReforgedLogger
from mcdreforged.permission_manager import PermissionLevel
from mcdreforged.plugin.operation_result import SingleOperationResult, PluginOperationResult
from mcdreforged.plugin.plugin_event import EventListener, LiteralEvent, PluginEvent
from mcdreforged.plugin.plugin_registry import DEFAULT_LISTENER_PRIORITY, HelpMessage
from mcdreforged.rtext import RTextBase, RText
from mcdreforged.server_status import ServerStatus
from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged import MCDReforgedServer
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.plugin import RegularPlugin


def log_call(func):
	"""
	Log plugin call
	Use kwarg is_plugin_call to determined if do log
	"""
	def wrap(self, *args, **kwargs):
		is_plugin_call = 'is_plugin_call'
		if kwargs.get(is_plugin_call, True):
			self.logger.debug('Plugin called {}(), args amount: {}'.format(func.__name__, len(args)))
			for arg in args:
				self.logger.debug('  - type: {}, content: {}'.format(type(arg).__name__, arg))
		if is_plugin_call in kwargs:
			kwargs.pop(is_plugin_call)
		return func(self, *args, **kwargs)
	return wrap


def return_if_success(func):
	"""
	Catch all exception from the func execution
	Return a bool, if no exception occurred
	"""
	def wrap(self, *args, **kwargs):
		try:
			func(self, *args, **kwargs)
			return True
		except:
			self.logger.debug('Exception occurred when calling {}: '.format(func), exc_info=True)
			return False
	return wrap


class ServerInterface:
	MCDR = True  # Identifier for plugins

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.__mcdr_server = mcdr_server
		self.logger = mcdr_server.logger

	# ------------------------
	#      Server Control
	# ------------------------

	@log_call
	def start(self):
		"""
		Start the server

		:return: If the action succeed it's True. If the server is running or being starting by other plugin return False
		:rtype: bool
		"""
		return self.__mcdr_server.start_server()

	@log_call
	def stop(self):
		"""
		Soft shutting down the server by sending the correct stop command to the server

		:rtype: None
		"""
		self.__mcdr_server.set_exit_naturally(False)
		self.__mcdr_server.stop(forced=False)

	@log_call
	def wait_for_start(self):
		"""
		Wait until the server is stopped, or is able to start

		:rtype: None
		"""
		while self.is_server_running(is_plugin_call=False):
			time.sleep(0.01)

	@log_call
	def restart(self):
		"""
		Restart the server
		It will first soft stop the server and then wait until the server is stopped, then start the server up

		:rtype: None
		"""
		self.stop(is_plugin_call=False)
		self.wait_for_start(is_plugin_call=False)
		self.start(is_plugin_call=False)

	@log_call
	def stop_exit(self):
		"""
		Soft stop the server and exit MCDR

		:rtype: None
		"""
		self.__mcdr_server.stop(forced=False)

	@log_call
	def exit(self):
		"""
		Exit MCDR when the server is stopped
		If the server is running return False otherwise return True

		:raise: IllegalCallError, if the server is not stopped
		"""
		if self.__mcdr_server.is_server_running():
			raise IllegalCallError('Cannot exit MCDR when the server is running')
		self.__mcdr_server.set_server_status(ServerStatus.STOPPED)

	@log_call
	def is_server_running(self):
		"""
		Return if the server is running

		:rtype: bool
		"""
		return self.__mcdr_server.is_server_running()

	@log_call
	def is_server_startup(self):
		"""
		Return if the server has started up

		:rtype: bool
		"""
		return self.__mcdr_server.is_server_startup()

	@log_call
	def is_rcon_running(self):
		"""
		Return if MCDR's rcon is running

		:rtype: bool
		"""
		return self.__mcdr_server.rcon_manager.is_running()

	@log_call
	def get_server_pid(self):
		"""
		Return the pid of the server process
		Notes the process with this pid is a bash process, which is the parent process of real server process
		you might be interested in

		:return: The pid of the server. None if the server is stopped
		:rtype: int or None
		"""
		if self.__mcdr_server.process is not None:
			return self.__mcdr_server.process.pid
		return None

	# ------------------------
	#     Text Interaction
	# ------------------------

	@log_call
	def execute(self, text, encoding=None):
		"""
		Execute a command by sending the command content to server's standard input stream

		:param str text: The content of the command you want to send
		:param str encoding: The encoding method for the text
		:rtype: None
		"""
		self.__mcdr_server.send(text, encoding=encoding)

	@log_call
	def tell(self, player, text, encoding=None):
		"""
		Use /tellraw <target> to send the message to the specific player

		:param str player: The name of the player you want to tell
		:param text: the message you want to send
		:param str encoding: The encoding method for the text
		:type text: str or dict or list or RTextBase
		:rtype: None
		"""
		if isinstance(text, RTextBase):
			content = text.to_json_str()
		else:
			content = json.dumps(str(text))
		self.execute('tellraw {} {}'.format(player, content), encoding=encoding, is_plugin_call=False)

	@log_call
	def say(self, text, encoding=None):
		"""
		Use /tellraw @a to broadcast the message in game

		:param text: the message you want to send
		:param str encoding: The encoding method for the text
		:type text: str or dict or list or RTextBase
		:rtype: None
		"""
		self.tell('@a', text, encoding=encoding, is_plugin_call=False)

	@log_call
	def reply(self, info, text, encoding=None):
		"""
		Reply to the source of the Info
		If the Info is from a player then use tell to reply the player
		Otherwise use logger.info to output to the console

		:param Info info: the Info you want to reply to
		:param text: the message you want to send
		:param str encoding: The encoding method for the text
		:type text: str or dict or list or RTextBase
		:rtype: None
		"""
		if info.is_player:
			self.tell(info.player, text, encoding=encoding, is_plugin_call=False)
		else:
			misc_util.print_text_to_console(self.logger, text)

	# ------------------------
	#     Plugin Operations
	# ------------------------

	# Notes: All plugin manipulation will trigger a dependency check, which might cause unwanted plugin operations

	def __check_if_success(self, operation_result: SingleOperationResult) -> bool:
		"""
		Check if there's any plugin inside the given operation result (load result / reload result etc.)
		Then check if the plugin passed the dependency check
		"""
		success = operation_result.has_success()
		if success:
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
		return self.__check_if_success(self.__mcdr_server.plugin_manager.last_operation_result.load_result)

	def __existed_regular_plugin_manipulate(self, plugin_id: str, handler: Callable[['PluginManager'], Callable[['RegularPlugin'], Any]], result_getter: Callable[[PluginOperationResult], SingleOperationResult]) -> bool or None:
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
			return self.__check_if_success(opt_result)
		return None

	@log_call
	def load_plugin(self, plugin_file_path):
		"""
		Load a plugin from the given path
		Example: "plugins/my_plugin.py"

		:param str plugin_file_path: a str, The name of the plugin to load
		:return: If the plugin gets loaded successfully
		:rtype: bool
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.load_plugin)

	@log_call
	def enable_plugin(self, plugin_file_path):
		"""
		Enable an unloaded plugin from the given path
		Example: "plugins/my_plugin.py.disabled"

		:param str plugin_file_path: The file path of the plugin to enable
		:return: If the plugin gets enabled successfully
		:rtype: bool
		"""
		return self.__not_loaded_regular_plugin_manipulate(plugin_file_path, lambda mgr: mgr.enable_plugin)

	@log_call
	def reload_plugin(self, plugin_id):
		"""
		Reload a plugin specified by plugin id
		Example: "my-plugin"

		:param str plugin_id: a str, the id of the plugin to reload
		:return: A bool indicating if the plugin gets reloaded successfully. None if plugin not found
		:rtype: bool or None
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.reload_plugin, lambda lor: lor.reload_result)

	@log_call
	def unload_plugin(self, plugin_id):
		"""
		Unload a plugin specified by plugin id
		Example: "my-plugin"

		:param str plugin_id: a str, the id of the plugin to reload
		:return: A bool indicating if the plugin gets unloaded successfully. None if plugin not found
		:rtype: bool or None
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.unload_plugin, lambda lor: lor.unload_result)

	@log_call
	def disable_plugin(self, plugin_id):
		"""
		Disable an unloaded plugin from the given path
		Example: "my-plugin"

		:param str plugin_id: The file path of the plugin to disable
		:return: A bool indicating if the plugin gets disabled successfully. None if plugin not found
		:rtype: bool or None
		"""
		return self.__existed_regular_plugin_manipulate(plugin_id, lambda mgr: mgr.disable_plugin, lambda lor: lor.unload_result)

	@log_call
	def refresh_all_plugins(self):
		"""
		Reload all plugins, load all new plugins and then unload all removed plugins
		"""
		self.__mcdr_server.plugin_manager.refresh_all_plugins()

	@log_call
	def refresh_changed_plugins(self):
		"""
		Reload all changed plugins, load all new plugins and then unload all removed plugins
		"""
		self.__mcdr_server.plugin_manager.refresh_changed_plugins()

	@log_call
	def get_plugin_list(self):
		"""
		Return a str list containing all loaded plugin id like ["my-plugin", "another-plugin"]

		:rtype: list[str]
		"""
		return [plugin.get_metadata().id for plugin in self.__mcdr_server.plugin_manager.get_regular_plugins()]

	def __existed_regular_plugin_info_getter(self, plugin_id: str, handler: Callable[['RegularPlugin'], Any]):
		plugin = self.__mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is not None:
			return handler(plugin)
		return None

	@log_call
	def get_plugin_metadata(self, plugin_id: str):
		return self.__existed_regular_plugin_info_getter(plugin_id, lambda plugin: plugin.get_metadata())

	@log_call
	def get_plugin_file_path(self, plugin_id: str):
		return self.__existed_regular_plugin_info_getter(plugin_id, lambda plugin: plugin.file_path)

	@log_call
	def get_plugin_instance(self, plugin_name):
		"""
		Return the current loaded plugin instance. with this your plugin can access the same plugin instance as MCDR
		It's quite important to use this instead of manually import the plugin you want if the target plugin needs to
		react to events of MCDR
		The plugin need to be in plugins/plugin_name.py

		:param str plugin_name: The name of the plugin you want. It can be "my_plugin" or "my_plugin.py"
		:return: A current loaded plugin instance. Return None if plugin not found
		"""
		plugin = self.__mcdr_server.plugin_manager.get_plugin(plugin_name)
		if plugin is not None:
			plugin = plugin.module
		return plugin

	# ------------------------
	#     Plugin Registry
	# ------------------------

	def __get_current_plugin(self):
		plugin = self.__mcdr_server.plugin_manager.get_current_running_plugin()
		if plugin.is_regular():
			return plugin
		else:
			raise IllegalCallError('MCDR provided thead is required')

	@log_call
	def add_help_message(self, prefix, message, permission=PermissionLevel.MINIMUM_LEVEL):
		"""
		Add a help message for the current plugin, which is used in !!help command

		:param str prefix: The help command of your plugin
		When player click on the displayed message it will suggest this prefix parameter to the player
		:param str or RTextBase message: A neat command description
		:param int permission: The minimum permission level for the user to see this help message. With default, anyone
		can see this message
		:raise: IllegalCallError if it's not called in a MCDR provided thread
		"""
		plugin = self.__get_current_plugin()
		if isinstance(message, str):
			message = RText(message)
		plugin.add_help_message(HelpMessage(plugin, prefix, message, permission))

	@log_call
	def add_event_listener(self, event: Union[PluginEvent, str], callback: Callable, priority: int = DEFAULT_LISTENER_PRIORITY):
		"""
		Add an event listener for the current plugin

		:param event: The id of the event to listen, or the PluginEvent instance if it's a built-in
		MCDR event
		:param callback: The callback listener method for the event
		:param priority: The priority of the listener
		:raise: IllegalCallError if it's not called in a MCDR provided thread
		"""
		plugin = self.__get_current_plugin()
		if isinstance(event, str):
			event = LiteralEvent(event_id=event)
		plugin.add_event_listener(event, EventListener(plugin, callback, priority))

	@log_call
	def add_command(self, root_node: Literal):
		"""
		Add an event listener for the current plugin

		:param root_node: the root node of your command tree
		:raise: IllegalCallError if it's not called in a MCDR provided thread
		"""
		plugin = self.__get_current_plugin()
		plugin.add_command(root_node)

	@log_call
	def dispatch_event(self, event: PluginEvent, args: Tuple[Any, ...]):
		"""
		Dispatch an event to all loaded plugins

		:param event: The event to dispatch
		:param args: The argument that will be used to invoke the event listeners. An server interface instance will be
		automatically added to the beginning of the paramenter list
		"""
		self.__mcdr_server.task_executor.execute_or_enqueue(lambda: self.__mcdr_server.plugin_manager.dispatch_event(event, args))

	# ------------------------
	#           Misc
	# ------------------------

	@log_call
	def get_permission_level(self, obj):
		"""
		Return the permission level number the parameter object has
		The object can be Info instance or a str, the name of a player
		Raise TypeError if the type of obj is object supported

		:param obj: The object your are querying
		:type obj: Info or str or CommandSource
		:return: The permission level you are querying
		:rtype: int
		:raise: TypeError
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
	def set_permission_level(self, player, value):
		"""
		Set the permission level of a player

		:param str player: The name of the player that you want to set his/her permission level
		:param value: The target permission level you want to set the player to. It can be an int or a str as long as
		it's related to the permission level. Available examples: 1, '1', 'user'
		:type value: int or str
		:raise: TypeError if param value is illegal
		"""
		level = PermissionLevel.get_level(value)
		if level is None:
			raise TypeError('Parameter level needs to be a permission related value')
		self.__mcdr_server.permission_manager.set_permission_level(player, value)

	@log_call
	def rcon_query(self, command):
		"""
		Send command to the server through rcon

		:param str command: The command you want to send to the rcon server
		:return: The result server returned from rcon. Return None if rcon is not running or rcon query failed
		:rtype: str or None
		"""
		return self.__mcdr_server.rcon_manager.send_command(command)

	@log_call
	def get_unique_logger(self) -> MCDReforgedLogger:
		plugin = self.__get_current_plugin()
		return MCDReforgedLogger(self.__mcdr_server, plugin.get_metadata().name)
