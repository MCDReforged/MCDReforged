"""
Plugin management
"""
import collections
import os
import queue
import threading
from contextlib import contextmanager
from typing import Callable, Dict, Optional, Any, Tuple, List, TYPE_CHECKING, Deque

from mcdreforged.constants import core_constant, plugin_constant
from mcdreforged.plugin import plugin_factory
from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin
from mcdreforged.plugin.builtin.python_plugin import PythonPlugin
from mcdreforged.plugin.meta.dependency_walker import DependencyWalker
from mcdreforged.plugin.operation_result import PluginOperationResult, SingleOperationResult
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, MCDREvent, EventListener
from mcdreforged.plugin.plugin_registry import PluginRegistryStorage
from mcdreforged.plugin.plugin_thread import PluginThreadPool
from mcdreforged.plugin.type.permanent_plugin import PermanentPlugin
from mcdreforged.plugin.type.plugin import AbstractPlugin, PluginState
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils import file_util, string_util, misc_util, class_util
from mcdreforged.utils.future import Future
from mcdreforged.utils.logger import DebugOption
from mcdreforged.utils.thread_local_storage import ThreadLocalStorage

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class PluginManager:
	TLS_PLUGIN_KEY = 'current_plugin'

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.plugin_directories = []  # type: List[str]
		self.mcdr_server = mcdr_server
		self.logger = mcdr_server.logger

		# plugin storage, id -> Plugin
		self.plugins: Dict[str, AbstractPlugin] = {}
		# file_path -> id mapping
		self.plugin_file_path: Dict[str, str] = {}
		# storage for event listeners, help messages and commands
		self.registry_storage = PluginRegistryStorage(self)

		# not used currently
		self.thread_pool = PluginThreadPool(self.mcdr_server, max_thread=core_constant.PLUGIN_THREAD_POOL_SIZE)

		# thread local storage, to store current plugin
		self.__tls = ThreadLocalStorage()

		# plugin manipulation logics
		self.__mani_lock = threading.RLock()
		self.__mani_thread: Optional[threading.Thread] = None
		self.__mani_queue = queue.Queue()

	@classmethod
	def touch_directory(cls):
		file_util.touch_directory(plugin_constant.PLUGIN_CONFIG_DIRECTORY)

	# --------------------------
	#   Getters / Setters etc.
	# --------------------------

	def get_current_running_plugin(self, *, thread=None) -> Optional[AbstractPlugin]:
		"""
		Get current executing plugin in this thread
		:param thread: If specified, it should be a Thread instance. Then it will return the executing plugin in the given thread
		"""
		stack = self.__tls.get(self.TLS_PLUGIN_KEY, None, thread=thread)  # type: Deque[AbstractPlugin]
		return stack[-1] if stack is not None else None

	def get_plugin_amount(self) -> int:
		return len(self.plugins)

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

	def set_plugin_directories(self, plugin_directories: Optional[List[str]]):
		if plugin_directories is None:
			plugin_directories = []
		self.plugin_directories = misc_util.unique_list(plugin_directories)
		for plugin_directory in self.plugin_directories:
			file_util.touch_directory(plugin_directory)

	@contextmanager
	def with_plugin_context(self, plugin: AbstractPlugin):
		stack = self.__tls.get(self.TLS_PLUGIN_KEY, default=collections.deque())  # type: Deque[AbstractPlugin]
		stack.append(plugin)
		self.__tls.put(self.TLS_PLUGIN_KEY, stack)
		try:
			yield
		finally:
			stack.pop()
			if len(stack) == 0:
				self.__tls.pop(self.TLS_PLUGIN_KEY)

	def contains_plugin_file(self, file_path: str) -> bool:
		"""
		Check if the given path corresponds to an already loaded plugin
		"""
		return os.path.abspath(file_path) in self.plugin_file_path

	def contains_plugin_id(self, plugin_id: str) -> bool:
		"""
		Check if the given plugin id represents a loaded plugin
		Includes permanent plugins
		"""
		return plugin_id in self.plugins

	# ---------------------------------------
	#   Permanent build-in plugin operation
	# ---------------------------------------

	def __add_permanent_plugin(self, plugin: PermanentPlugin):
		self.__add_plugin(plugin)
		plugin.set_state(PluginState.LOADED)
		plugin.load()
		plugin.set_state(PluginState.READY)

	def register_permanent_plugins(self):
		self.__add_permanent_plugin(MCDReforgedPlugin(self))
		self.__add_permanent_plugin(PythonPlugin(self))
		self.__sort_plugins_by_id()
		self.__update_registry()

	# ------------------------------------------------
	#   Actual operations that add / remove a plugin
	# ------------------------------------------------

	def __add_plugin(self, plugin: AbstractPlugin):
		plugin_id = plugin.get_id()
		if plugin_id in self.plugins:
			self.logger.critical('Something is not correct, a plugin with existed plugin id "{}" is added'.format(plugin_id))
		self.plugins[plugin_id] = plugin
		if isinstance(plugin, RegularPlugin):
			self.plugin_file_path[os.path.abspath(plugin.plugin_path)] = plugin_id

	def __remove_plugin(self, plugin: AbstractPlugin):
		if not plugin.is_permanent():
			plugin_id = plugin.get_id()
			self.plugins.pop(plugin_id, None)
			if isinstance(plugin, RegularPlugin):
				self.plugin_file_path.pop(os.path.abspath(plugin.plugin_path), None)

	# ----------------------------
	#   Single Plugin Operations
	# ----------------------------

	def __load_plugin(self, file_path: str) -> Optional[RegularPlugin]:
		"""
		Try to load a plugin from the given file
		If succeeds, add the plugin to the plugin list, the plugin state will be set to LOADED
		If fails, nothing will happen
		:param file_path: The path to the plugin file
		:return: the new plugin instance if succeeds, otherwise None
		"""
		plugin = plugin_factory.create_regular_plugin(self, file_path)
		try:
			plugin.load()
		except:
			self.logger.exception(self.mcdr_server.tr('plugin_manager.load_plugin.fail', plugin.get_name()))
			return None
		else:
			existed_plugin = self.plugins.get(plugin.get_id())
			if existed_plugin is None:
				self.__add_plugin(plugin)
				self.logger.info(self.mcdr_server.tr('plugin_manager.load_plugin.success', plugin.get_name()))
				return plugin
			else:
				self.logger.error(self.mcdr_server.tr('plugin_manager.load_plugin.duplicate', plugin.get_name(), plugin.plugin_path, existed_plugin.get_name(), existed_plugin.plugin_path))
				try:
					plugin.unload()
				except:
					# should never come here
					self.logger.exception(self.mcdr_server.tr('plugin_manager.load_plugin.unload_duplication_fail', plugin.get_name(), plugin.plugin_path))
				plugin.remove()  # quickly remove this plugin
				return None

	def __unload_plugin(self, plugin: AbstractPlugin) -> bool:
		"""
		Try to load a plugin from the given file
		Whether it succeeds or not, the plugin instance will be removed from the plugin list
		The plugin state will be set to UNLOADING
		:return: If there's an exception during plugin unloading
		"""
		try:
			plugin.unload()
		except:
			# should never come here
			plugin.set_state(PluginState.UNLOADING)  # a fallback set state
			self.logger.exception(self.mcdr_server.tr('plugin_manager.unload_plugin.fail', plugin.get_name()))
			ret = False
		else:
			self.logger.info(self.mcdr_server.tr('plugin_manager.unload_plugin.success', plugin.get_name()))
			plugin.receive_event(MCDRPluginEvents.PLUGIN_UNLOADED, ())
			ret = True
		finally:
			self.__remove_plugin(plugin)
		return ret

	def __reload_plugin(self, plugin: AbstractPlugin) -> bool:
		"""
		Try to reload an existed and unloaded plugin
		If fails, unload the plugin and then the plugin state will be set to UNLOADED
		:return: If the plugin reloads successfully without error
		"""
		try:
			plugin.reload()
		except:
			self.logger.exception(self.mcdr_server.tr('plugin_manager.reload_plugin.fail', plugin.get_name()))
			self.__unload_plugin(plugin)
			return False
		else:
			# in case the plugin id changes into an existed plugin id
			existed_plugin = self.plugins.get(plugin.get_id())
			if existed_plugin is None:
				self.__add_plugin(plugin)
				self.logger.info(self.mcdr_server.tr('plugin_manager.reload_plugin.success', plugin.get_name()))
				return True
			else:
				self.logger.error(self.mcdr_server.tr('plugin_manager.load_plugin.duplicate', plugin.get_name(), plugin.plugin_path, existed_plugin.get_name(), existed_plugin.plugin_path))
				try:
					plugin.unload()
				except:
					# should never come here
					self.logger.exception(self.mcdr_server.tr('plugin_manager.load_plugin.unload_duplication_fail', plugin.get_name(), plugin.plugin_path))
				return False

	# ---------------------------------------
	#   Regular Plugin Collector & Handlers
	# ---------------------------------------

	def __collect_possible_plugin_file_paths(self) -> List[str]:
		paths = []
		for plugin_directory in self.plugin_directories:
			if os.path.isdir(plugin_directory):
				for file in os.listdir(plugin_directory):
					file_path = os.path.join(plugin_directory, file)
					if plugin_factory.is_plugin(file_path):
						paths.append(file_path)
			else:
				self.logger.warning('Plugin directory "{}" not found'.format(plugin_directory))
		return paths

	def __collect_and_process_new_plugins(self, filter_: Callable[[str], bool], *, possible_paths: Optional[List[str]] = None) -> SingleOperationResult:
		"""
		:param filter_: A str predicate function for testing if the plugin file path is acceptable
		:param possible_paths: Optional. If you have already done self.__collect_possible_plugin_file_paths() before,
		you can pass the previous result as the argument to reuse that, so less time cost
		"""
		if possible_paths is None:
			possible_paths = self.__collect_possible_plugin_file_paths()

		result = SingleOperationResult()
		for file_path in possible_paths:
			if not self.contains_plugin_file(file_path) and filter_(file_path):
				plugin = self.__load_plugin(file_path)
				if plugin is None:
					result.fail(file_path)
				else:
					result.succeed(plugin)
		return result

	def __collect_regular_plugins(
			self, select_filter: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin],
			operation_name: str = 'operate', collect_filter: Callable[[RegularPlugin], bool] = lambda p: True
	) -> List[RegularPlugin]:
		"""
		collected = selected + affected
		:return: A list of plugin in topo order
		"""
		plugin_list = self.get_regular_plugins() if specific is None else [specific]
		selected_plugins = list(filter(select_filter, plugin_list))
		selected_plugins_set = set(selected_plugins)

		walker = DependencyWalker(self)
		walker.walk()
		affected_plugin_ids: List[str] = []

		for plugin in selected_plugins:
			affected_plugin_ids.extend(walker.get_children(plugin.get_id()))

		collected_plugins: List[RegularPlugin] = []  # plugins, in topo order
		for plugin_id in sorted(misc_util.unique_list(affected_plugin_ids), key=walker.get_topo_order):
			plugin = self.get_regular_plugin_from_id(plugin_id)
			assert plugin is not None
			if collect_filter(plugin):
				collected_plugins.append(plugin)

		affected_plugins = list(filter(lambda plg: plg not in selected_plugins_set, collected_plugins))
		if self.logger.should_log_debug(DebugOption.PLUGIN):
			self.logger.debug('Collected {}x plugin'.format(len(collected_plugins)) + ':' if len(collected_plugins) > 0 else '', no_check=True)
			if len(collected_plugins) > 0:
				self.logger.debug('- selected {}x: {}'.format(len(selected_plugins), ', '.join(map(str, selected_plugins))), no_check=True)
				self.logger.debug('- affected {}x: {}'.format(len(affected_plugins), ', '.join(map(str, affected_plugins))), no_check=True)
		if len(affected_plugins) > 0:
			self.logger.info('Collected {}x extra plugins for {} due to dependency associations: {}'.format(len(affected_plugins), operation_name, ', '.join(map(str, affected_plugins))))

		return collected_plugins

	def __unload_given_plugins(self, filter_: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> SingleOperationResult:
		affected_plugins = self.__collect_regular_plugins(filter_, specific, 'unload')
		result = SingleOperationResult()
		for plugin in affected_plugins:
			result.record(plugin, self.__unload_plugin(plugin))
		return result

	def __reload_ready_plugins(self, filter_: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> SingleOperationResult:
		def state_check(plg: RegularPlugin):
			return plg.in_states({PluginState.READY})

		affected_plugins = self.__collect_regular_plugins(lambda plg: state_check(plg) and filter_(plg), specific, 'reload', state_check)
		result = SingleOperationResult()

		# child first, parent last
		for plugin in reversed(affected_plugins):
			self.__unload_plugin(plugin)

		# parent first, child last
		# actually the order is not sensitive here, but why not
		for plugin in affected_plugins:
			result.record(plugin, self.__reload_plugin(plugin))
		return result

	# ---------------------------
	#   Multi-Plugin Operations
	# ---------------------------

	# Current behavior for plugin operations
	#
	# Steps to take
	#   load: load, check dept, finalization
	#   unload: unload, finalization
	#   reload: unload, load, check dept, finalization
	#
	# Common path: unload, load, check dept, finalization
	#
	# In detailed:
	# 1. Do unload in reversed topo order:
	#   a. dispatch plugin unload event
	#   b. unload plugin object
	#
	# 2. Load plugins
	# 3. Check dependencies
	#
	# 4. Finalization (:meth:`__finalization_plugin_manipulation`)
	#   a. Remove / Get-ready plugin objects
	#   b. Do load in topo order: dispatch on_load event
	#   c. Update registry
	#   d. Sort plugins
	#
	# When to dispatch load/unload event:
	# - load: after dept check
	# - unload: immediately
	#
	# New sync operations will be queued and delayed
	#   see :meth:`__run_manipulation`

	def __finalization_plugin_manipulation(
			self, load_result: Optional[SingleOperationResult] = None, unload_result: Optional[SingleOperationResult] = None,
			reload_result: Optional[SingleOperationResult] = None
	) -> PluginOperationResult:
		"""
		When returns, all events / operations are finished processing
		"""
		if load_result is None:
			load_result = SingleOperationResult()
		if unload_result is None:
			unload_result = SingleOperationResult()
		if reload_result is None:
			reload_result = SingleOperationResult()

		walker = DependencyWalker(self)
		walk_result = walker.walk()
		dependency_check_result = SingleOperationResult()  # topo order in success_list
		for item in walk_result:
			plugin = self.plugins[item.plugin_id]
			dependency_check_result.record(plugin, item.success)
			if not item.success:
				self.logger.error(self.mcdr_server.tr('plugin_manager.check_plugin_dependencies.item_failed', plugin, item.reason))
				self.__unload_plugin(plugin)

		self.logger.debug(self.mcdr_server.tr('plugin_manager.check_plugin_dependencies.topo_order'), option=DebugOption.PLUGIN)
		for plugin in dependency_check_result.success_list:
			self.logger.debug('- {}'.format(plugin), option=DebugOption.PLUGIN)

		# Expected plugin states:
		#                   success_list        fail_list
		# load_result       LOADED              N/A
		# unload_result     UNLOADING           UNLOADING
		# reload_result     LOADED              UNLOADING
		# dep_chk_result    LOADED              UNLOADING

		self.registry_storage.clear()  # in case plugin invokes dispatch_event during on_load. don't let them trigger listeners

		newly_loaded_plugins = {*load_result.success_list, *reload_result.success_list}
		to_be_removed_plugins = unload_result.success_list + unload_result.failed_list + reload_result.failed_list + dependency_check_result.failed_list

		# collect removed plugin module instance in case e.g. reloading when a plugin file was renamed
		# so its on_load event can still have the old entry module
		removed_plugins_module_instance = {}
		for plugin in to_be_removed_plugins:
			if isinstance(plugin, RegularPlugin):
				removed_plugins_module_instance[plugin.get_id()] = plugin.entry_module_instance

		# do remove
		for plugin in to_be_removed_plugins:
			plugin.remove()

		# get ready
		for plugin in dependency_check_result.success_list:
			if plugin in newly_loaded_plugins:
				plugin.ready()

		# PLUGIN_LOADED event
		for plugin in dependency_check_result.success_list:
			if plugin in newly_loaded_plugins:
				if isinstance(plugin, RegularPlugin):
					old_entry_module_instance = plugin.old_entry_module_instance
					if old_entry_module_instance is None:
						old_entry_module_instance = removed_plugins_module_instance.get(plugin.get_id(), None)
					plugin.receive_event(MCDRPluginEvents.PLUGIN_LOADED, (old_entry_module_instance,))

		# they should all be ready
		for plugin in self.get_regular_plugins():
			plugin.assert_state({PluginState.READY})

		self.__update_registry()
		self.__sort_plugins_by_id()

		return PluginOperationResult(load_result, unload_result, reload_result, dependency_check_result)

	def __sort_plugins_by_id(self):
		self.plugins = dict(sorted(map(tuple, self.plugins.items()), key=lambda item: item[0]))

	def __update_registry(self):
		self.registry_storage.clear()
		for plugin in self.get_all_plugins():
			self.registry_storage.collect(plugin.plugin_registry)
		self.registry_storage.arrange()
		self.mcdr_server.on_plugin_registry_changed()

	def __refresh_plugins(self, reload_filter: Callable[[RegularPlugin], bool]) -> PluginOperationResult:
		possible_paths = self.__collect_possible_plugin_file_paths()
		possible_paths_set = set(possible_paths)
		unload_result = self.__unload_given_plugins(lambda plugin: not plugin.plugin_exists() or plugin.plugin_path not in possible_paths_set)
		load_result = self.__collect_and_process_new_plugins(lambda fp: True, possible_paths=possible_paths)
		reload_result = self.__reload_ready_plugins(reload_filter)
		return self.__finalization_plugin_manipulation(load_result, unload_result, reload_result)

	# --------------
	#   Interfaces
	# --------------

	def __run_manipulation(self, action: Callable[[], PluginOperationResult]) -> Future[PluginOperationResult]:
		"""
		Async manipulations: Blocked and wait via self.__mani_lock

		Sync manipulations: Run directly for the 1st action, store in queue for other actions.
		The delayed actions in queue will be executed after the 1st action is done

		:return: A future to the plugin operation result. The future is finished
		iif. it's the 1st manipulation call in the current thread's call chain
		"""
		with self.__mani_lock:
			future: Future[PluginOperationResult] = Future()
			self.__mani_queue.put((action, future))
			if self.__mani_thread != threading.current_thread():
				self.__mani_thread = threading.current_thread()
				try:
					while True:
						try:
							queued_action, queued_future = self.__mani_queue.get_nowait()
						except queue.Empty:
							break
						else:
							result = queued_action()
							queued_future.set_result(result)
				finally:
					self.__mani_thread = None
			else:
				self.logger.debug('Detected chained sync plugin manipulation, queueing', option=DebugOption.PLUGIN)

			return future

	def load_plugin(self, file_path: str) -> Future[PluginOperationResult]:
		def load_plugin_action() -> PluginOperationResult:
			self.logger.info(self.mcdr_server.tr('plugin_manager.load_plugin.entered', file_path))
			load_result = self.__collect_and_process_new_plugins(lambda fp: fp == file_path)
			return self.__finalization_plugin_manipulation(load_result=load_result)

		class_util.check_type(file_path, str)
		return self.__run_manipulation(load_plugin_action)

	def unload_plugin(self, plugin: RegularPlugin) -> Future[PluginOperationResult]:
		def unload_plugin_action() -> PluginOperationResult:
			self.logger.info(self.mcdr_server.tr('plugin_manager.unload_plugin.entered', plugin))
			unload_result = self.__unload_given_plugins(lambda plg: True, specific=plugin)
			return self.__finalization_plugin_manipulation(unload_result=unload_result)

		class_util.check_type(plugin, RegularPlugin)
		return self.__run_manipulation(unload_plugin_action)

	def reload_plugin(self, plugin: RegularPlugin) -> Future[PluginOperationResult]:
		def reload_plugin_action() -> PluginOperationResult:
			self.logger.info(self.mcdr_server.tr('plugin_manager.reload_plugin.entered', plugin))
			reload_result = self.__reload_ready_plugins(lambda plg: True, specific=plugin)
			return self.__finalization_plugin_manipulation(reload_result=reload_result)

		class_util.check_type(plugin, RegularPlugin)
		return self.__run_manipulation(reload_plugin_action)

	def enable_plugin(self, file_path: str) -> Future[PluginOperationResult]:
		class_util.check_type(file_path, str)
		self.logger.info(self.mcdr_server.tr('plugin_manager.enable_plugin.entered', file_path))
		new_file_path = string_util.remove_suffix(file_path, plugin_constant.DISABLED_PLUGIN_FILE_SUFFIX)
		if plugin_factory.is_disabled_plugin(file_path):
			os.rename(file_path, new_file_path)
			return self.load_plugin(new_file_path)
		else:
			return Future.completed(PluginOperationResult.of_empty())

	def disable_plugin(self, plugin: RegularPlugin) -> Future[PluginOperationResult]:
		def done_callback(_: PluginOperationResult):
			if plugin.plugin_exists():
				os.rename(plugin.plugin_path, plugin.plugin_path + plugin_constant.DISABLED_PLUGIN_FILE_SUFFIX)

		self.logger.info(self.mcdr_server.tr('plugin_manager.disable_plugin.entered', plugin))
		future = self.unload_plugin(plugin)
		future.add_done_callback(done_callback)
		return future

	def refresh_all_plugins(self) -> Future[PluginOperationResult]:
		def refresh_all_plugins_action() -> PluginOperationResult:
			self.logger.info(self.mcdr_server.tr('plugin_manager.refresh_all_plugins.entered'))
			return self.__refresh_plugins(lambda plg: True)

		return self.__run_manipulation(refresh_all_plugins_action)

	def refresh_changed_plugins(self) -> Future[PluginOperationResult]:
		def refresh_changed_plugins_action() -> PluginOperationResult:
			self.logger.info(self.mcdr_server.tr('plugin_manager.refresh_changed_plugins.entered'))
			return self.__refresh_plugins(lambda plg: plg.file_changed())

		return self.__run_manipulation(refresh_changed_plugins_action)

	# ----------------
	#   Plugin Event
	# ----------------

	def __dispatch_event(self, event: MCDREvent, args: Tuple[Any, ...]):
		"""
		Event dispatch logic implementation
		"""
		self.logger.debug('Dispatching {} with args ({})'.format(event, ', '.join([type(arg).__name__ for arg in args])), option=DebugOption.PLUGIN)
		for listener in self.registry_storage.event_listeners.get(event.id, []):
			self.trigger_listener(listener, args)

	def dispatch_event(self, event: MCDREvent, args: Tuple[Any, ...], *, on_executor_thread: bool = True, block: bool = False, timeout: Optional[float] = None):
		"""
		Event dispatching interface
		"""
		if on_executor_thread:
			self.mcdr_server.task_executor.execute_on_thread(lambda: self.__dispatch_event(event, args), block=block, timeout=timeout)
		else:
			self.__dispatch_event(event, args)

	def trigger_listener(self, listener: EventListener, args: Tuple[Any, ...]):
		"""
		Event listener triggering implementation
		The server_interface parameter will be automatically added as the 1st parameter
		"""
		try:
			with self.with_plugin_context(listener.plugin):
				listener.execute(listener.plugin.server_interface, *args)
		except:
			self.logger.exception('Error invoking listener {}'.format(listener))
