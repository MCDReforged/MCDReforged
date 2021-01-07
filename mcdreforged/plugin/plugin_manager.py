"""
Plugin management
"""
import os
import sys
import threading
from typing import Callable, Dict, Optional, Any, Tuple, List, TYPE_CHECKING

from mcdreforged import constant
from mcdreforged.logger import DebugOption
from mcdreforged.plugin.dependency_walker import DependencyWalker
from mcdreforged.plugin.mcdreforged_plugin import MCDReforgedPlugin
from mcdreforged.plugin.operation_result import PluginOperationResult, SingleOperationResult
from mcdreforged.plugin.plugin import PluginState, AbstractPlugin
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, MCDREvent, EventListener
from mcdreforged.plugin.plugin_registry import PluginManagerRegistry
from mcdreforged.plugin.plugin_thread import PluginThreadPool
from mcdreforged.plugin.regular_plugin import RegularPlugin
from mcdreforged.utils import file_util, string_util, misc_util

if TYPE_CHECKING:
	from mcdreforged import MCDReforgedServer


class PluginManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.plugin_folders = []  # type: List[str]
		self.mcdr_server = mcdr_server
		self.logger = mcdr_server.logger

		# id -> Plugin plugin storage
		self.plugins = {}   # type: Dict[str, AbstractPlugin]
		# file_path -> id mapping
		self.plugin_file_path = {}  # type: Dict[str, str]
		# storage for event listeners, help messages and commands
		self.registry_storage = PluginManagerRegistry(self)

		self.last_operation_result = PluginOperationResult(self)

		self.thread_pool = PluginThreadPool(self.mcdr_server, max_thread=constant.PLUGIN_THREAD_POOL_SIZE)
		self.tls = threading.local()
		self.set_current_plugin(None)

		file_util.touch_folder(constant.PLUGIN_CONFIG_FOLDER)

	# --------------------------
	#   Getters / Setters etc.
	# --------------------------

	def get_current_running_plugin(self) -> Optional[RegularPlugin]:
		"""
		Get current executing plugin in this thread
		"""
		return self.tls.current_plugin

	def get_all_plugins(self) -> List[AbstractPlugin]:
		return list(self.plugins.values())

	def get_regular_plugins(self) -> List[RegularPlugin]:
		return [plugin for plugin in self.plugins.values() if isinstance(plugin, RegularPlugin)]

	def get_plugin_from_id(self, plugin_id: str) -> Optional[AbstractPlugin]:
		return self.plugins.get(plugin_id)

	def get_regular_plugin_from_id(self, plugin_id: str) -> Optional[RegularPlugin]:
		plugin = self.get_plugin_from_id(plugin_id)
		if not isinstance(plugin, RegularPlugin):
			plugin = None
		return plugin

	def set_current_plugin(self, plugin: Optional[AbstractPlugin]):
		self.tls.current_plugin = plugin

	def set_plugin_folders(self, plugin_folders: List[str]):
		for plugin_folder in self.plugin_folders:
			try:
				sys.path.remove(plugin_folder)
			except ValueError:
				self.logger.exception('Fail to remove old plugin folder "{}" in sys.path'.format(plugin_folder))
		self.plugin_folders = misc_util.unique_list(plugin_folders)
		for plugin_folder in self.plugin_folders:
			file_util.touch_folder(plugin_folder)
			sys.path.append(plugin_folder)

	def contains_plugin_file(self, file_path: str) -> bool:
		return file_path in self.plugin_file_path

	def contains_plugin_id(self, plugin_id: str) -> bool:
		"""
		Includes permanent plugins
		"""
		return plugin_id in self.plugins

	# ---------------------------------------
	#   Permanent build-in plugin operation
	# ---------------------------------------

	def __add_permanent_plugin(self, plugin: AbstractPlugin):
		self.__add_plugin(plugin)
		plugin.load()

	def register_permanent_plugins(self):
		self.__add_permanent_plugin(MCDReforgedPlugin(self))
		self.__update_registry()  # not really necessary, but in case

	# ------------------------------------------------
	#   Actual operations that add / remove a plugin
	# ------------------------------------------------

	def __add_plugin(self, plugin: AbstractPlugin):
		plugin_id = plugin.get_metadata().id
		self.plugins[plugin_id] = plugin
		if isinstance(plugin, RegularPlugin):
			self.plugin_file_path[plugin.file_path] = plugin_id

	def __remove_plugin(self, plugin: AbstractPlugin):
		if not plugin.is_permanent():
			self.plugins.pop(plugin.get_metadata().id)
			if isinstance(plugin, RegularPlugin):
				self.plugin_file_path.pop(plugin.file_path)

	# ----------------------------
	#   Single Plugin Operations
	# ----------------------------

	def __load_plugin(self, file_path):
		"""
		Try to load a plugin from the given file
		If succeeds, add the plugin to the plugin list, the plugin state will be set to LOADED
		If fails, nothing will happen
		:param str file_path: The path to the plugin file, a *.py
		:return: the new plugin instance if succeeds, otherwise None
		:rtype: RegularPlugin or None
		"""
		plugin = RegularPlugin(self, file_path)
		try:
			plugin.load()
		except:
			self.logger.exception(self.mcdr_server.tr('plugin_manager.load_plugin.fail', plugin.get_name()))
			return None
		else:
			existed_plugin = self.plugins.get(plugin.get_metadata().id)
			if existed_plugin is None:
				self.logger.info(self.mcdr_server.tr('plugin_manager.load_plugin.success', plugin.get_name()))
				self.__add_plugin(plugin)
				return plugin
			else:
				self.logger.error(self.mcdr_server.tr('plugin_manager.load_plugin.duplicate', plugin.get_name(), plugin.file_path, existed_plugin.get_name(), existed_plugin.file_path))
				try:
					plugin.unload()
				except:
					# should never come here
					self.logger.exception(self.mcdr_server.tr('plugin_manager.load_plugin.unload_duplication_fail', plugin.get_name(), plugin.file_path))
				plugin.remove()  # quickly remove this plugin
				return None

	def __unload_plugin(self, plugin):
		"""
		Try to load a plugin from the given file
		Whether it succeeds or not, the plugin instance will be removed from the plugin list
		The plugin state will be set to UNLOADING
		:param AbstractPlugin plugin: The plugin instance to be unloaded
		:return: If there's an exception during plugin unloading
		:rtype: bool
		"""
		try:
			plugin.unload()
		except:
			# should never come here
			plugin.set_state(PluginState.UNLOADING)
			self.logger.exception(self.mcdr_server.tr('plugin_manager.unload_plugin.unload_fail', plugin.get_name()))
			ret = False
		else:
			self.logger.info(self.mcdr_server.tr('plugin_manager.unload_plugin.unload_success', plugin.get_name()))
			ret = True
		finally:
			self.__remove_plugin(plugin)
		return ret

	def __reload_plugin(self, plugin):
		"""
		Try to reload an existed plugin
		If fails, unload the plugin and then the plugin state will be set to UNLOADED
		:param AbstractPlugin plugin: The plugin instance to be reloaded
		:return: If the plugin reloads successfully without error
		:rtype: bool
		"""
		try:
			plugin.reload()
		except:
			self.logger.exception(self.mcdr_server.tr('plugin_manager.reload_plugin.fail', plugin.get_name()))
			self.__unload_plugin(plugin)
			return False
		else:
			self.logger.info(self.mcdr_server.tr('plugin_manager.reload_plugin.success', plugin.get_name()))
			return True

	# ---------------------------------------
	#   Regular Plugin Collector & Handlers
	# ---------------------------------------

	def collect_and_process_new_plugins(self, filter: Callable[[str], bool]) -> SingleOperationResult:
		result = SingleOperationResult()
		for plugin_folder in self.plugin_folders:
			file_list = file_util.list_file_with_suffix(plugin_folder, constant.PLUGIN_FILE_SUFFIX)
			for file_path in file_list:
				if not self.contains_plugin_file(file_path) and filter(file_path):
					plugin = self.__load_plugin(file_path)
					if plugin is None:
						result.fail(file_path)
					else:
						result.succeed(plugin)
		return result

	def collect_and_remove_plugins(self, filter: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> SingleOperationResult:
		result = SingleOperationResult()
		plugin_list = self.get_regular_plugins() if specific is None else [specific]
		for plugin in plugin_list:
			if filter(plugin):
				result.record(plugin, self.__unload_plugin(plugin))
		return result

	def reload_ready_plugins(self, filter: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> SingleOperationResult:
		result = SingleOperationResult()
		plugin_list = self.get_regular_plugins() if specific is None else [specific]
		for plugin in plugin_list:
			if plugin.in_states({PluginState.READY}) and filter(plugin):
				result.record(plugin, self.__reload_plugin(plugin))
		return result

	def check_plugin_dependencies(self) -> SingleOperationResult:
		result = SingleOperationResult()
		walker = DependencyWalker(self)
		for item in walker.walk():
			plugin = self.plugins.get(item.plugin_id)  # should be not None
			result.record(plugin, item.success)
			if not item.success:
				self.logger.error('Unloading plugin {} due to {}'.format(plugin, item.reason))
				self.__unload_plugin(plugin)
		self.logger.debug('Plugin dependency topology order:', option=DebugOption.PLUGIN)
		for plugin in result.success_list:
			self.logger.debug('- {}'.format(plugin), option=DebugOption.PLUGIN)
		# the success list order matches the dependency topo order
		return result

	# ---------------------------
	#   Multi-Plugin Operations
	# ---------------------------

	# MCDR 0.x behavior for reload
	# 1. reload existed (and changed) plugins. if reload fail unload it
	# 2. load new plugins, and ignore those plugins which just got unloaded because reloading failed
	# 3. unload removed plugins
	# 4. call on_load for new loaded plugins

	# Current behavior for plugin operations
	# 1. Actual plugin operations
	#   For plugin refresh
	#     1. Load new plugins
	#     2. Unload plugins whose file is removed
	#     3. Reload existed (and matches filter) plugins whose state is ready. if reload fail unload it
	#
	#   For single plugin operation
	#     1. Enable / disable plugin
	#
	# 2. Plugin Processing  (method __post_plugin_process)
	#     1. Check dependencies, unload plugins that has dependencies not satisfied
	#     2. Call on_load for new / reloaded plugins by topo order
	#     3. Call on_unload for unloaded plugins

	def __check_thread(self):
		if not self.mcdr_server.task_executor.is_on_thread():
			raise RuntimeError('Plugin operations should be executed directly on task executor\'s thread, but thread {} founded'.format(threading.current_thread().getName()))

	def __post_plugin_process(self, load_result=None, unload_result=None, reload_result=None):
		if load_result is None:
			load_result = SingleOperationResult()
		if unload_result is None:
			unload_result = SingleOperationResult()
		if reload_result is None:
			reload_result = SingleOperationResult()

		dependency_check_result = self.check_plugin_dependencies()
		self.last_operation_result.record(load_result, unload_result, reload_result, dependency_check_result)

		# Expected plugin states:
		# 					success_list		fail_list
		# load_result		LOADED				N/A
		# unload_result		UNLOADING			UNLOADING
		# reload_result		READY				UNLOADING
		# dep_chk_result	LOADED / READY		UNLOADING

		for plugin in load_result.success_list + reload_result.success_list:
			if plugin in dependency_check_result.success_list:
				plugin.ready()

		newly_loaded_plugins = {*load_result.success_list, *reload_result.success_list}
		for plugin in dependency_check_result.success_list:
			if plugin in newly_loaded_plugins:
				if isinstance(plugin, RegularPlugin):
					plugin.receive_event(MCDRPluginEvents.PLUGIN_LOAD, (plugin.old_module_instance,))

		for plugin in unload_result.success_list + unload_result.failed_list + reload_result.failed_list + dependency_check_result.failed_list:
			plugin.assert_state({PluginState.UNLOADING})
			# plugins might just be newly loaded but failed on dependency check, dont dispatch event to them
			if plugin not in load_result.success_list:
				plugin.receive_event(MCDRPluginEvents.PLUGIN_UNLOAD, ())
			plugin.remove()

		# they should be
		for plugin in self.get_regular_plugins():
			plugin.assert_state({PluginState.READY})

		self.__update_registry()

	def __refresh_plugins(self, reload_filter: Callable[[RegularPlugin], bool]):
		self.__check_thread()
		load_result = self.collect_and_process_new_plugins(lambda fp: True)
		unload_result = self.collect_and_remove_plugins(lambda plugin: not plugin.file_exists())
		reload_result = self.reload_ready_plugins(reload_filter)
		self.__post_plugin_process(load_result, unload_result, reload_result)

	def __update_registry(self):
		self.registry_storage.clear()
		for plugin in self.get_all_plugins():
			self.registry_storage.collect(plugin.plugin_registry)
		self.registry_storage.arrange()
		self.mcdr_server.on_plugin_changed()

	# --------------
	#   Interfaces
	# --------------

	def load_plugin(self, file_path: str):
		self.__check_thread()
		self.logger.info('Loading plugin from {}'.format(file_path))
		load_result = self.collect_and_process_new_plugins(lambda fp: fp == file_path)
		self.__post_plugin_process(load_result=load_result)

	def unload_plugin(self, plugin: RegularPlugin):
		self.__check_thread()
		self.logger.info('Unloading plugin {}'.format(plugin))
		unload_result = self.collect_and_remove_plugins(lambda plg: True, specific=plugin)
		self.__post_plugin_process(unload_result=unload_result)

	def reload_plugin(self, plugin: RegularPlugin):
		self.__check_thread()
		self.logger.info('Reloading plugin {}'.format(plugin))
		reload_result = self.reload_ready_plugins(lambda plg: True, specific=plugin)
		self.__post_plugin_process(reload_result=reload_result)

	def enable_plugin(self, file_path):
		self.logger.info('Enabling plugin from {}'.format(file_path))
		new_file_path = string_util.remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
		if os.path.isfile(file_path):
			os.rename(file_path, new_file_path)
			self.load_plugin(new_file_path)

	def disable_plugin(self, plugin: RegularPlugin):
		self.logger.info('Disabling plugin {}'.format(plugin))
		self.unload_plugin(plugin)
		if os.path.isfile(plugin.file_path):
			os.rename(plugin.file_path, plugin.file_path + constant.DISABLED_PLUGIN_FILE_SUFFIX)

	def refresh_all_plugins(self):
		self.logger.info('Refreshing all plugins')
		return self.__refresh_plugins(lambda plg: True)

	def refresh_changed_plugins(self):
		self.logger.info('Refreshing all changed plugins')
		return self.__refresh_plugins(lambda plg: plg.file_changed())

	# ----------------
	#   Plugin Event
	# ----------------

	def dispatch_event(self, event: MCDREvent, args: Tuple[Any, ...]):
		self.logger.debug('Dispatching {} with args ({})'.format(event, ', '.join([type(arg).__name__ for arg in args])), option=DebugOption.PLUGIN)
		for listener in self.registry_storage.event_listeners.get(event.id, []):
			self.trigger_listener(listener, args)

	def trigger_listener(self, listener: EventListener, args: Tuple[Any, ...]):
		"""
		The terminated entry for triggering a listener
		The server_interface parameter will be automatically added as the 1st parameter
		"""
		# self.thread_pool.add_task(lambda: listener.execute(*args), listener.plugin)
		self.set_current_plugin(listener.plugin)
		try:
			listener.execute(self.mcdr_server.server_interface, *args)
		except:
			self.logger.exception('Error invoking listener {}'.format(listener))
		finally:
			self.set_current_plugin(None)
