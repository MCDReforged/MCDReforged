"""
Plugin management
"""
import os
from typing import Callable, Dict, List, Optional

from mcdr import tool, constant
from mcdr.exception import IllegalCall
from mcdr.logger import Logger
from mcdr.plugin.dependency_walker import DependencyWalker
from mcdr.plugin.plugin import Plugin, PluginState
from mcdr.plugin.plugin_event import PluginEvent
from mcdr.plugin.plugin_thread import PluginThreadPool
from mcdr.rtext import RTextList, RText, RAction, RTextBase


class SingleOperationResult:
	def __init__(self):
		self.success_list = []  # type: List[Plugin]
		self.failed_list = []  # type: List[Plugin or str]

	def succeed(self, plugin: Plugin):
		self.success_list.append(plugin)

	def fail(self, plugin: Plugin or str):
		self.failed_list.append(plugin)

	def record(self, plugin: Plugin or str, result: bool):
		if result:
			self.succeed(plugin)
		else:
			self.fail(plugin)


class PluginOperationResult:
	load_result: SingleOperationResult
	unload_result: SingleOperationResult
	reload_result: SingleOperationResult
	dependency_check_result: SingleOperationResult

	def __init__(self, plugin_manager):
		self.plugin_manager = plugin_manager
		self.server = plugin_manager.server
		self.has_record = False

	def record(self, load_result, unload_result, reload_result, dependencies_resolve_result):
		self.has_record = True
		self.load_result = load_result
		self.unload_result = unload_result
		self.reload_result = reload_result
		self.dependency_check_result = dependencies_resolve_result

	def to_rtext(self) -> RTextBase:
		if not self.has_record:
			raise IllegalCall('No record yet')

		def add_element(msg: RTextList, element):
			msg.append(element)
			msg.append('; ')

		def add_if_not_empty(msg: RTextList, lst: List[Plugin or str], key: str):
			if len(lst) > 0:
				add_element(msg, RText(self.server.t(key, len(lst))).h('\n'.join(map(str, lst))))

		message = RTextList()
		add_if_not_empty(message, self.load_result.success_list, 'plugin_manager.__refresh_plugins.info_loaded_succeeded')
		add_if_not_empty(message, self.unload_result.success_list, 'plugin_manager.__refresh_plugins.info_unloaded_succeeded')
		add_if_not_empty(message, self.reload_result.success_list, 'plugin_manager.__refresh_plugins.info_reloaded_succeeded')
		add_if_not_empty(message, self.load_result.failed_list, 'plugin_manager.__refresh_plugins.info_loaded_failed')
		add_if_not_empty(message, self.unload_result.failed_list, 'plugin_manager.__refresh_plugins.info_unloaded_failed')
		add_if_not_empty(message, self.reload_result.failed_list, 'plugin_manager.__refresh_plugins.info_reloaded_failed')
		add_if_not_empty(message, self.dependency_check_result.failed_list, 'plugin_manager.__refresh_plugins.info_dependency_check_failed')
		if message.empty():
			add_element(message, self.server.t('plugin_manager.__refresh_plugins.info_none'))
		message.append(
			RText(self.server.t('plugin_manager.__refresh_plugins.info_plugin_amount', len(self.plugin_manager.plugins))).
				h('\n'.join(map(str, self.plugin_manager.plugins.values()))).
				c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return message


class PluginManager:
	def __init__(self, server, plugin_folder):
		self.plugin_folder = plugin_folder
		self.server = server
		self.logger = server.logger  # type: Logger

		# id -> Plugin plugin storage
		self.plugins = {}   # type: Dict[str, Plugin]
		# file_path -> id mapping
		self.plugin_file_path = {}  # type: Dict[str, str]

		self.last_operation_result = PluginOperationResult(self)

		self.thread_pool = PluginThreadPool(self.server, max_thread=constant.PLUGIN_THREAD_POOL_SIZE)

		tool.touch_folder(self.plugin_folder)
		tool.touch_folder(constant.PLUGIN_CONFIG_FOLDER)

	def contains_plugin_file(self, file_path):
		return file_path in self.plugin_file_path

	def contains_plugin_id(self, plugin_id):
		return plugin_id in self.plugins

	# ------------------------------------------------
	#   Actual operations that add / remove a plugin
	# ------------------------------------------------

	def __add_plugin(self, plugin: Plugin):
		self.plugins.pop(plugin.get_meta_data().id)
		self.plugin_file_path.pop(plugin.file_path)

	def __remove_plugin(self, plugin: Plugin):
		self.plugins.pop(plugin.get_meta_data().id)
		self.plugin_file_path.pop(plugin.file_path)

	# ----------------------------
	#   Single Plugin Operations
	# ----------------------------

	def __load_plugin(self, file_path):
		"""
		Try to load a plugin from the given file
		If succeeds, add the plugin to the plugin list
		If fails, nothing will happen
		:param str file_path: The path to the plugin file, a *.py
		:return: the new plugin instance if succeeds, otherwise None
		:rtype: Plugin or None
		"""
		plugin = Plugin(self, file_path)
		try:
			plugin.load()
			self.logger.info(self.server.t('plugin_manager.load_plugin.success', repr(plugin)))
		except:
			self.logger.exception(self.server.t('plugin_manager.load_plugin.fail', repr(plugin)))
			return None
		else:
			self.__add_plugin(plugin)
			return plugin

	def __unload_plugin(self, plugin):
		"""
		Try to load a plugin from the given file
		Whether it succeeds or not, the plugin instance will be removed from the plugin list
		:param Plugin plugin: The plugin instance to be unloaded
		:return: If there's an exception during plugin unloading
		:rtype: bool
		"""
		try:
			plugin.unload()
		except:
			self.logger.exception(self.server.t('plugin_manager.unload_plugin.unload_fail', repr(plugin)))
			ret = False
		else:
			self.logger.info(self.server.t('plugin_manager.unload_plugin.unload_success', repr(plugin)))
			ret = True
		finally:
			self.__remove_plugin(plugin)
		return ret

	def __reload_plugin(self, plugin):
		"""
		Try to load a plugin from the given file
		If succeeds, add the plugin to the plugin list
		If fails, nothing will happen
		:param Plugin plugin: The plugin instance to be reloaded
		:return: If the plugin reloads successfully without error
		:rtype: bool
		"""
		try:
			plugin.reload()
		except:
			self.logger.exception(self.server.t('plugin_manager.reload_plugin.fail', repr(plugin)))
			self.__unload_plugin(plugin)
			return False
		else:
			self.logger.info(self.server.t('plugin_manager.reload_plugin.success', repr(plugin)))
			return True

	# -------------------------------
	#   Plugin Collector & Handlers
	# -------------------------------

	def collect_and_process_new_plugins(self, filter: Callable[[str], bool], specific: Optional[str] = None) -> SingleOperationResult:
		result = SingleOperationResult()
		file_list = tool.list_file(self.plugin_folder, constant.PLUGIN_FILE_SUFFIX) if specific is None else [specific]
		for file_path in file_list:
			if not self.contains_plugin_file(file_path) and filter(file_path):
				plugin = self.__load_plugin(file_path)
				if plugin is None:
					result.fail(file_path)
				else:
					result.succeed(plugin)
		return result

	def collect_and_remove_plugins(self, filter: Callable[[Plugin], bool], specific: Optional[Plugin] = None) -> SingleOperationResult:
		result = SingleOperationResult()
		plugin_list = self.plugins.values() if specific is None else [specific]
		for plugin in plugin_list:
			if filter(plugin):
				result.record(plugin, self.__unload_plugin(plugin))
		return result

	def reload_ready_plugins(self, filter: Callable[[Plugin], bool], specific: Optional[Plugin] = None) -> SingleOperationResult:
		result = SingleOperationResult()
		plugin_list = self.plugins.values() if specific is None else [specific]
		for plugin in plugin_list:
			if filter(plugin):
				result.record(plugin, self.__reload_plugin(plugin))
				self.__reload_plugin(plugin)
		return result

	def check_plugin_dependencies(self) -> SingleOperationResult:
		result = SingleOperationResult()
		walker = DependencyWalker(self)
		for item in walker.walk():
			plugin = self.plugins.get(item.plugin_id)  # should be not None
			result.record(plugin, item.success)
			if not item.success:
				self.logger.warning('Unloading plugin {} due to {}'.format(plugin, item.reason))
				self.__unload_plugin(plugin)
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

	def __post_plugin_process(self, load_result=None, unload_result=None, reload_result=None):
		if load_result is None:
			load_result = SingleOperationResult()
		if unload_result is None:
			unload_result = SingleOperationResult()
		if reload_result is None:
			reload_result = SingleOperationResult()

		dependency_check_result = self.check_plugin_dependencies()
		self.last_operation_result.record(load_result, unload_result, reload_result, dependency_check_result)

		for plugin in load_result.success_list:
			plugin.assert_state({PluginState.LOADED})
			plugin.set_state(PluginState.READY)

		newly_loaded_plugins = {*load_result.success_list, *reload_result.success_list}
		for plugin in dependency_check_result.success_list:
			if plugin in newly_loaded_plugins:
				plugin.receive_event(PluginEvent.ON_PLUGIN_LOAD)

		for plugin in unload_result.success_list + unload_result.failed_list + reload_result.failed_list + dependency_check_result.failed_list:
			plugin.receive_event(PluginEvent.ON_PLUGIN_UNLOAD)

	def __refresh_plugins(self, reload_filter: Callable[[Plugin], bool]):
		load_result = self.collect_and_process_new_plugins(lambda fp: True)
		unload_result = self.collect_and_remove_plugins(lambda plugin: not plugin.file_exists())
		reload_result = self.reload_ready_plugins(reload_filter)
		self.__post_plugin_process(load_result, unload_result, reload_result)

	# --------------
	#   Interfaces
	# --------------

	def load_plugin(self, file_path: str):
		load_result = self.collect_and_process_new_plugins(lambda fp: True, specific=file_path)
		self.__post_plugin_process(load_result=load_result)

	def unload_plugin(self, plugin: Plugin):
		unload_result = self.collect_and_remove_plugins(lambda plg: True, specific=plugin)
		self.__post_plugin_process(unload_result=unload_result)

	def reload_plugin(self, plugin: Plugin):
		reload_result = self.reload_ready_plugins(lambda plg: True, specific=plugin)
		self.__post_plugin_process(reload_result=reload_result)

	def enable_plugin(self, file_path):
		new_file_path = tool.remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
		if os.path.isfile(file_path):
			os.rename(file_path, new_file_path)
			self.load_plugin(new_file_path)

	def disable_plugin(self, file_path):
		plugin_id = self.plugin_file_path.get(file_path)
		if plugin_id is not None:
			self.unload_plugin(self.plugins.get(plugin_id))
		if os.path.isfile(file_path):
			os.rename(file_path, file_path + constant.DISABLED_PLUGIN_FILE_SUFFIX)

	def refresh_all_plugins(self):
		return self.__refresh_plugins(lambda plg: True)

	def refresh_changed_plugins(self):
		return self.__refresh_plugins(lambda plg: plg.file_changed())
