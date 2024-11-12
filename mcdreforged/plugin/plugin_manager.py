"""
Plugin management
"""
import dataclasses
import enum
import functools
import os
import queue
import threading
from concurrent.futures import Future
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
from typing import Callable, Dict, Optional, Any, Tuple, List, TYPE_CHECKING

from mcdreforged.constants import plugin_constant
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.mcdr_config import MCDReforgedConfig
from mcdreforged.plugin import plugin_factory
from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin
from mcdreforged.plugin.builtin.python_plugin import PythonPlugin
from mcdreforged.plugin.exception import RequirementCheckFailure
from mcdreforged.plugin.meta.dependency_walker import DependencyWalker
from mcdreforged.plugin.operation_result import PluginOperationResult, SingleOperationResult
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import PluginRegistryStorage
from mcdreforged.plugin.type.builtin_plugin import BuiltinPlugin
from mcdreforged.plugin.type.common import PluginState
from mcdreforged.plugin.type.plugin import AbstractPlugin
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils import file_utils, string_utils, misc_utils, class_utils, path_utils, function_utils, future_utils
from mcdreforged.utils.exception import SelfJoinError
from mcdreforged.utils.types.path_like import PathStr

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class PluginManager:
	TLS_PLUGIN_KEY = 'current_plugin'

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.plugin_directories: List[Path] = []
		self.mcdr_server = mcdr_server
		self.logger = mcdr_server.logger
		self.__tr = mcdr_server.create_internal_translator('plugin_manager').tr

		# plugin storage, id -> Plugin
		self.__plugins: Dict[str, AbstractPlugin] = {}
		# absolute file_path -> id mapping
		self.__plugin_file_paths: Dict[Path, str] = {}
		# storage for event listeners, help messages and commands
		self.registry_storage = PluginRegistryStorage(self)

		# thread local storage, to store current plugin
		self.__current_plugin: ContextVar[Optional[AbstractPlugin]] = ContextVar('tls', default=None)

		# plugin manipulation logics
		self.__mani_lock = threading.RLock()
		self.__mani_thread: Optional[threading.Thread] = None
		self.__mani_queue = queue.Queue()

		mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, config: MCDReforgedConfig, log: bool):
		self.set_plugin_directories(config.plugin_directories)
		if log:
			self.logger.info(self.__tr('on_config_changed.plugin_directories_set'))
			for directory in self.plugin_directories:
				self.logger.info('- {}'.format(directory))

	@classmethod
	def touch_directory(cls):
		file_utils.touch_directory(plugin_constant.PLUGIN_CONFIG_DIRECTORY)

	# --------------------------
	#   Getters / Setters etc.
	# --------------------------

	def get_plugin_in_current_context(self) -> Optional[AbstractPlugin]:
		"""
		Get current executing plugin in the current thread
		"""
		return self.__current_plugin.get()

	@contextmanager
	def with_plugin_context(self, plugin: AbstractPlugin):
		token = self.__current_plugin.set(plugin)
		try:
			yield
		finally:
			self.__current_plugin.reset(token)

	def get_plugin_amount(self) -> int:
		return len(self.__plugins)

	def get_all_plugins(self) -> List[AbstractPlugin]:
		return list(self.__plugins.values())

	def get_regular_plugins(self) -> List[RegularPlugin]:
		return [plugin for plugin in self.__plugins.values() if isinstance(plugin, RegularPlugin)]

	def get_plugin_from_id(self, plugin_id: str) -> Optional[AbstractPlugin]:
		return self.__plugins.get(plugin_id)

	def get_regular_plugin_from_id(self, plugin_id: str) -> Optional[RegularPlugin]:
		plugin = self.get_plugin_from_id(plugin_id)
		if not isinstance(plugin, RegularPlugin):
			plugin = None
		return plugin

	def set_plugin_directories(self, plugin_directories: Optional[List[str]]):
		if plugin_directories is None:
			plugin_directories = []
		self.plugin_directories = [Path(pd) for pd in misc_utils.unique_list(plugin_directories)]
		for plugin_directory in self.plugin_directories:
			file_utils.touch_directory(plugin_directory)

	def contains_plugin_file(self, file_path: PathStr) -> bool:
		"""
		Check if the given path corresponds to an already loaded plugin
		"""
		return Path(file_path).absolute() in self.__plugin_file_paths

	def contains_plugin_id(self, plugin_id: str) -> bool:
		"""
		Check if the given plugin id represents a loaded plugin
		Includes builtin plugins
		"""
		return plugin_id in self.__plugins

	def verify_plugin_path_to_load(self, plugin_path: PathStr):
		path = Path(plugin_path).absolute()
		for plugin_dir in self.plugin_directories:
			if path_utils.is_relative_to(path, Path(plugin_dir).absolute()):
				return True
		return False

	# ---------------------------------------
	#   Builtin plugin operation
	# ---------------------------------------

	def __add_builtin_plugin(self, plugin: BuiltinPlugin):
		self.__add_plugin(plugin)
		plugin.set_state(PluginState.LOADED)
		plugin.load()
		plugin.set_state(PluginState.READY)

	def register_builtin_plugins(self):
		self.__add_builtin_plugin(MCDReforgedPlugin(self))
		self.__add_builtin_plugin(PythonPlugin(self))
		self.__sort_plugins_by_id()
		self.__update_registry()

	# ------------------------------------------------
	#   Actual operations that add / remove a plugin
	# ------------------------------------------------

	def __add_plugin(self, plugin: AbstractPlugin):
		plugin_id = plugin.get_id()
		if plugin_id in self.__plugins:
			self.logger.critical('Something is not correct, a plugin with existed plugin id "{}" is added'.format(plugin_id))
		self.__plugins[plugin_id] = plugin
		if isinstance(plugin, RegularPlugin):
			self.__plugin_file_paths[plugin.plugin_path.absolute()] = plugin_id

	def __remove_plugin(self, plugin: AbstractPlugin):
		if not plugin.is_builtin():
			plugin_id = plugin.get_id()
			self.__plugins.pop(plugin_id, None)
			if isinstance(plugin, RegularPlugin):
				self.__plugin_file_paths.pop(plugin.plugin_path.absolute(), None)

	# ----------------------------
	#   Single Plugin Operations
	# ----------------------------

	@classmethod
	def __make_plugin_path(cls, plg: AbstractPlugin) -> Any:
		if isinstance(plg, RegularPlugin):
			return str(plg.plugin_path)
		elif isinstance(plg, BuiltinPlugin):
			return '@@builtin@@'
		else:
			return None

	def __load_plugin(self, file_path: Path) -> Optional[RegularPlugin]:
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
		except Exception as e:
			if isinstance(e, RequirementCheckFailure):
				self.logger.error(self.__tr('load_plugin.fail', plugin.get_name()))
				self.logger.error(self.__tr('load_plugin.resolution_error', plugin.get_name(), str(e)))
			else:
				self.logger.exception(self.__tr('load_plugin.fail', plugin.get_name()))
			return None
		else:
			existed_plugin = self.__plugins.get(plugin.get_id())
			if existed_plugin is None:
				self.__add_plugin(plugin)
				self.logger.info(self.__tr('load_plugin.success', plugin.get_name()))
				return plugin
			else:
				self.logger.error(self.__tr('load_plugin.duplicate', plugin.get_name(), plugin.plugin_path, existed_plugin.get_name(), self.__make_plugin_path(existed_plugin)))
				try:
					plugin.unload()
				except Exception:
					# should never come here
					self.logger.exception(self.__tr('load_plugin.unload_duplication_fail', plugin.get_name(), plugin.plugin_path))
				plugin.remove()  # quickly remove this plugin
				return None

	def __unload_plugin(self, plugin: AbstractPlugin) -> bool:
		"""
		Try to load a plugin from the given file
		Whether it succeeds or not, the plugin instance will be removed from the plugin list
		The plugin state will be set to UNLOADING
		:return: If there's an exception during plugin unloading
		"""
		if plugin.in_states({PluginState.READY}):
			plugin.receive_event(MCDRPluginEvents.PLUGIN_UNLOADED, ())
		try:
			plugin.unload()
		except Exception:
			# should never come here
			plugin.set_state(PluginState.UNLOADING)  # a fallback set state
			self.logger.exception(self.__tr('unload_plugin.fail', plugin.get_name()))
			ret = False
		else:
			self.logger.info(self.__tr('unload_plugin.success', plugin.get_name()))
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
		except Exception as e:
			if isinstance(e, RequirementCheckFailure):
				self.logger.error(self.__tr('reload_plugin.fail', plugin.get_name()))
				self.logger.error(self.__tr('load_plugin.resolution_error', plugin.get_name(), str(e)))
			else:
				self.logger.exception(self.__tr('reload_plugin.fail', plugin.get_name()))
			self.__unload_plugin(plugin)
			return False
		else:
			# in case the plugin id changes into an existed plugin id
			existed_plugin = self.__plugins.get(plugin.get_id())
			if existed_plugin is None:
				self.__add_plugin(plugin)
				self.logger.info(self.__tr('reload_plugin.success', plugin.get_name()))
				return True
			else:
				self.logger.error(self.__tr('load_plugin.duplicate', plugin.get_name(), self.__make_plugin_path(plugin), existed_plugin.get_name(), self.__make_plugin_path(existed_plugin)))
				try:
					plugin.unload()
				except Exception:
					# should never come here
					self.logger.exception(self.__tr('load_plugin.unload_duplication_fail', plugin.get_name(), self.__make_plugin_path(plugin)))
				return False

	# ---------------------------------------
	#   Regular Plugin Collector & Handlers
	# ---------------------------------------

	def __collect_possible_plugin_file_paths(self) -> List[Path]:
		paths: List[Path] = []
		for plugin_directory in self.plugin_directories:
			if plugin_directory.is_dir():
				for file in os.listdir(plugin_directory):
					file_path = plugin_directory / file
					if plugin_factory.is_plugin(file_path):
						paths.append(file_path)
			else:
				self.logger.warning('Plugin directory "{}" not found'.format(plugin_directory))
		return paths

	def __load_given_new_plugins(self, plugin_paths: List[Path]) -> SingleOperationResult:
		result = SingleOperationResult()
		for file_path in plugin_paths:
			if (ex_pid := self.__plugin_file_paths.get(file_path.absolute())) is not None:
				self.logger.warning('Skipped loading of an existing plugin {} at {}'.format(ex_pid, file_path))
				result.fail(file_path)
				continue

			plugin = self.__load_plugin(file_path)
			if plugin is None:
				result.fail(file_path)
			else:
				result.succeed(plugin)
		return result

	def __collect_new_plugins(self, collect_filter: Callable[[Path], bool], *, possible_paths: Optional[List[Path]] = None) -> List[Path]:
		"""
		:param collect_filter: A str predicate function for testing if the plugin file path is acceptable
		:param possible_paths: Optional. If you have already done self.__collect_possible_plugin_file_paths() before,
		you can pass the previous result as the argument to reuse that, so less time cost
		"""
		if possible_paths is None:
			possible_paths = self.__collect_possible_plugin_file_paths()

		plugin_paths = []
		for file_path in possible_paths:
			if not self.contains_plugin_file(file_path) and collect_filter(file_path):
				plugin_paths.append(file_path)
		return plugin_paths

	def __collect_and_load_new_plugins(self, collect_filter: Callable[[Path], bool], *, possible_paths: Optional[List[Path]] = None) -> SingleOperationResult:
		"""
		:param collect_filter: A str predicate function for testing if the plugin file path is acceptable
		:param possible_paths: Optional. If you have already done self.__collect_possible_plugin_file_paths() before,
		you can pass the previous result as the argument to reuse that, so less time cost
		"""
		return self.__load_given_new_plugins(self.__collect_new_plugins(collect_filter, possible_paths=possible_paths))

	@dataclasses.dataclass(frozen=True)
	class __CollectWithDependentsResult:
		all: List[RegularPlugin]
		indirect: List[RegularPlugin]

	def __collect_regular_plugins_with_dependents(
			self, select_filter: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin],
			operation_name: str = 'operate', collect_filter: Callable[[RegularPlugin], bool] = function_utils.TRUE
	) -> __CollectWithDependentsResult:
		"""
		collected = selected + affected
		:return: A list of plugin in topo order
		"""
		plugin_list = self.get_regular_plugins() if specific is None else [specific]
		selected_plugins: List[RegularPlugin] = list(filter(select_filter, plugin_list))
		selected_plugins_set = set(selected_plugins)

		walker = DependencyWalker(self)
		walker.walk()
		affected_plugin_ids: List[str] = []

		for plugin in selected_plugins:
			affected_plugin_ids.extend(walker.get_children(plugin.get_id()))

		collected_plugins: List[RegularPlugin] = []  # plugins, in topo order
		for plugin_id in sorted(misc_utils.unique_list(affected_plugin_ids), key=walker.get_topo_order):
			plugin = self.get_regular_plugin_from_id(plugin_id)
			assert plugin is not None
			if collect_filter(plugin):
				collected_plugins.append(plugin)

		indirect_plugins = [plg for plg in collected_plugins if plg not in selected_plugins_set]
		if self.logger.should_log_debug(DebugOption.PLUGIN):
			self.logger.mdebug('Collected {}x plugin'.format(len(collected_plugins)) + (':' if len(collected_plugins) > 0 else ''), no_check=True)
			if len(collected_plugins) > 0:
				self.logger.mdebug('- selected {}x: {}'.format(len(selected_plugins), ', '.join(map(str, selected_plugins))), no_check=True)
				self.logger.mdebug('- affected {}x: {}'.format(len(indirect_plugins), ', '.join(map(str, indirect_plugins))), no_check=True)
		if len(indirect_plugins) > 0:
			self.logger.info('Collected {}x extra plugins for {} due to dependency associations: {}'.format(
				len(indirect_plugins), operation_name, ', '.join(map(str, indirect_plugins))
			))

		return self.__CollectWithDependentsResult(all=collected_plugins, indirect=indirect_plugins)

	@dataclasses.dataclass(frozen=True)
	class __UnloadGivenPluginResult:
		result: SingleOperationResult
		indirect: List[RegularPlugin]

	def __unload_given_plugins(self, filter_: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> __UnloadGivenPluginResult:
		affected_plugins = self.__collect_regular_plugins_with_dependents(filter_, specific, 'unload')
		result = SingleOperationResult()
		for plugin in affected_plugins.all:
			result.record(plugin, self.__unload_plugin(plugin))
		return self.__UnloadGivenPluginResult(result=result, indirect=affected_plugins.indirect)

	def __reload_ready_plugins(self, filter_: Callable[[RegularPlugin], bool], specific: Optional[RegularPlugin] = None) -> SingleOperationResult:
		def ready_state_check(plg: RegularPlugin) -> bool:
			return plg.in_states({PluginState.READY})

		def select_filter(plg: RegularPlugin) -> bool:
			return ready_state_check(plg) and filter_(plg)

		affected_plugins = self.__collect_regular_plugins_with_dependents(select_filter, specific, 'reload', ready_state_check).all
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

	def __finalize_plugin_manipulation(
			self,
			load_result: Optional[SingleOperationResult] = None,
			unload_result: Optional[SingleOperationResult] = None,
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
			plugin = self.__plugins[item.plugin_id]
			dependency_check_result.record(plugin, item.success)
			if not item.success:
				self.logger.error(self.__tr('check_plugin_dependencies.item_failed', plugin, item.reason))
				self.__unload_plugin(plugin)

		self.logger.mdebug(self.__tr('check_plugin_dependencies.topo_order'), option=DebugOption.PLUGIN)
		for plugin in dependency_check_result.success_list:
			self.logger.mdebug('- {}'.format(plugin), option=DebugOption.PLUGIN)

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
		self.__plugins = {plugin_id: self.__plugins[plugin_id] for plugin_id in sorted(self.__plugins.keys())}

	def __update_registry(self):
		self.registry_storage.clear()
		for plugin in self.get_all_plugins():
			self.registry_storage.collect(plugin, plugin.plugin_registry)
		self.registry_storage.arrange()
		self.mcdr_server.on_plugin_registry_changed()

	def __refresh_plugins(self, reload_filter: Callable[[RegularPlugin], bool]) -> PluginOperationResult:
		possible_paths = self.__collect_possible_plugin_file_paths()
		possible_paths_set = set(possible_paths)

		def unload_select_filter(plg: RegularPlugin) -> bool:
			return not plg.file_exists() or plg.plugin_path not in possible_paths_set

		unload_result = self.__unload_given_plugins(unload_select_filter).result
		load_result = self.__collect_and_load_new_plugins(function_utils.TRUE, possible_paths=possible_paths)  # indirect plugin will be collected inside __collect_new_plugins
		reload_result = self.__reload_ready_plugins(reload_filter)

		return self.__finalize_plugin_manipulation(load_result, unload_result, reload_result)

	# --------------
	#   Interfaces
	# --------------

	def __run_manipulation(self, action: Callable[[], PluginOperationResult], *, wait_if_async: bool = True) -> 'Future[PluginOperationResult]':
		"""
		Async manipulations: Submit to the task executor, then wait until the execution finished

		Sync manipulations (should be on the task executor thread): Run directly for the 1st action,
		store in queue for other actions. The delayed actions in queue will be executed after the 1st action is done

		:return: A future to the plugin operation result. The future is finished
		iif. it's the 1st manipulation call in the current thread's call chain
		"""
		if not self.mcdr_server.task_executor.is_on_thread():
			def func():
				self.__run_manipulation(action).add_done_callback(result_future.set_result)
			result_future = Future()
			executor_future = self.mcdr_server.task_executor.submit(func)
			if wait_if_async:
				executor_future.result()
			return result_future

		with self.__mani_lock:
			future: 'Future[PluginOperationResult]' = Future()
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
				self.logger.mdebug('Detected chained sync plugin manipulation, queueing', option=DebugOption.PLUGIN)

			return future

	def manipulate_plugins(
			self, *,
			load: Optional[List[Path]] = None,
			unload: Optional[List[RegularPlugin]] = None,
			reload: Optional[List[RegularPlugin]] = None,
			enable: Optional[List[Path]] = None,
			disable: Optional[List[RegularPlugin]] = None,
			try_load_indirect_unloaded: bool = True,
			entered_callback: Optional[Callable[[], Any]] = None,
	) -> 'Future[PluginOperationResult]':
		to_load_paths: List[Path] = (load or []).copy()
		to_unload_plugins: List[RegularPlugin] = (unload or []) + (disable or [])
		to_reload_plugins: List[RegularPlugin] = (reload or []).copy()

		for path in to_load_paths:
			class_utils.check_type(path, Path)
		for plugin in to_unload_plugins:
			class_utils.check_type(plugin, RegularPlugin)
		for plugin in to_reload_plugins:
			class_utils.check_type(plugin, RegularPlugin)

		for path in (enable or []):
			if plugin_factory.is_disabled_plugin(path):
				new_file_path = path.parent / string_utils.remove_suffix(path.name, plugin_constant.DISABLED_PLUGIN_FILE_SUFFIX)
				if new_file_path.is_file():
					self.logger.warning('Overwriting existing file {}'.format(new_file_path))
				os.replace(path, new_file_path)
				to_load_paths.append(new_file_path)

		for path in to_load_paths:
			if not self.verify_plugin_path_to_load(path):
				raise ValueError('Given plugin path {!r} to load is outside of MCDR\'s possible plugin directories {}'.format(path, self.plugin_directories))

		to_unload_plugin_ids = {p.get_id() for p in to_unload_plugins}
		to_reload_plugin_ids = {p.get_id() for p in to_reload_plugins}

		if len(to_unload_plugin_ids) + len(to_load_paths) + len(to_reload_plugin_ids) == 0:
			if entered_callback is not None:
				entered_callback()
			return future_utils.completed(PluginOperationResult.of_empty())

		def manipulate_action():
			if entered_callback is not None:
				entered_callback()

			def is_to_unload_plugin(plg: RegularPlugin) -> bool:
				return plg.get_id() in to_unload_plugin_ids

			def is_to_reload_plugin(plg: RegularPlugin) -> bool:
				return plg.get_id() in to_reload_plugin_ids

			unload_result = self.__unload_given_plugins(is_to_unload_plugin)
			if try_load_indirect_unloaded:
				# give those indirectly-unloaded dependent plugins a chance to load again
				for indirect_plugin in unload_result.indirect:
					if indirect_plugin.file_exists():
						to_load_paths.append(indirect_plugin.plugin_path)
						self.logger.mdebug('Add indirect to_load path {!r}'.format(indirect_plugin.plugin_path), option=DebugOption.PLUGIN)
			load_result = self.__load_given_new_plugins(to_load_paths)
			reload_result = self.__reload_ready_plugins(is_to_reload_plugin)
			return self.__finalize_plugin_manipulation(load_result, unload_result.result, reload_result)

		def done_callback(_: 'Future[PluginOperationResult]'):
			for plg in (disable or []):
				if plg.file_exists():
					disabled_path = plg.plugin_path.parent / (plg.plugin_path.name + plugin_constant.DISABLED_PLUGIN_FILE_SUFFIX)
					if disabled_path.is_file():
						self.logger.warning('Overwriting existing file {}'.format(disabled_path))
					os.replace(plg.plugin_path, disabled_path)

		future = self.__run_manipulation(manipulate_action)
		future.add_done_callback(done_callback)
		return future

	def load_plugin(self, file_path: Path) -> 'Future[PluginOperationResult]':
		class_utils.check_type(file_path, Path)

		def equals_to_the_given_path(fp: Path) -> bool:
			return fp == file_path

		return self.manipulate_plugins(
			load=self.__collect_new_plugins(equals_to_the_given_path),
			entered_callback=lambda: self.logger.info(self.__tr('load_plugin.entered', file_path)),
		)

	def unload_plugin(self, plugin: RegularPlugin) -> 'Future[PluginOperationResult]':
		class_utils.check_type(plugin, RegularPlugin)
		return self.manipulate_plugins(
			unload=[plugin],
			entered_callback=lambda: self.logger.info(self.__tr('unload_plugin.entered', plugin)),
		)

	def reload_plugin(self, plugin: RegularPlugin) -> 'Future[PluginOperationResult]':
		class_utils.check_type(plugin, RegularPlugin)
		return self.manipulate_plugins(
			reload=[plugin],
			entered_callback=lambda: self.logger.info(self.__tr('reload_plugin.entered', plugin)),
		)

	def enable_plugin(self, file_path: Path) -> 'Future[PluginOperationResult]':
		class_utils.check_type(file_path, Path)
		self.logger.info(self.__tr('enable_plugin.entered', file_path))
		return self.manipulate_plugins(enable=[file_path])

	def disable_plugin(self, plugin: RegularPlugin) -> 'Future[PluginOperationResult]':
		class_utils.check_type(plugin, RegularPlugin)
		self.logger.info(self.__tr('disable_plugin.entered', plugin))
		return self.manipulate_plugins(disable=[plugin])

	def refresh_all_plugins(self) -> 'Future[PluginOperationResult]':
		def refresh_all_plugins_action() -> PluginOperationResult:
			self.logger.info(self.__tr('refresh_all_plugins.entered'))
			return self.__refresh_plugins(function_utils.TRUE)

		return self.__run_manipulation(refresh_all_plugins_action)

	def refresh_changed_plugins(self) -> 'Future[PluginOperationResult]':
		def reload_filter(plg: RegularPlugin):
			return plg.file_changed()

		def refresh_changed_plugins_action() -> PluginOperationResult:
			self.logger.info(self.__tr('refresh_changed_plugins.entered'))
			return self.__refresh_plugins(reload_filter)

		return self.__run_manipulation(refresh_changed_plugins_action)

	# ----------------
	#   Plugin Event
	# ----------------

	class DispatchEventPolicy(enum.Enum):
		directly_invoke = enum.auto()
		ensure_on_thread = enum.auto()
		always_new_task = enum.auto()

	def dispatch_event(
			self, event: PluginEvent, args: Tuple[Any, ...], *,
			dispatch_policy: DispatchEventPolicy = DispatchEventPolicy.always_new_task, block: bool = False
	):
		"""
		Event dispatching interface
		"""
		if self.logger.should_log_debug(DebugOption.PLUGIN):
			self.logger.mdebug('Dispatching {} with args {}'.format(event, list(args)), no_check=True)

		is_on_executor_thread = self.mcdr_server.task_executor.is_on_thread()
		should_submit_task = (
				dispatch_policy == self.DispatchEventPolicy.always_new_task or
				dispatch_policy == self.DispatchEventPolicy.ensure_on_thread and not is_on_executor_thread
		)
		if block and should_submit_task and is_on_executor_thread:
			raise SelfJoinError()

		future1_list: List['Future[None]'] = []
		future2_list: List['Future[Future[None]]'] = []
		for listener in self.registry_storage.get_event_listeners(event.id):
			func: Callable[[], 'Future[None]'] = functools.partial(self.trigger_listener, listener, args)
			if should_submit_task:
				f2 = self.mcdr_server.task_executor.submit(func, plugin=listener.plugin)
				future2_list.append(f2)
			else:
				f1 = func()
				future1_list.append(f1)

		if block:
			for f2 in future2_list:
				future1_list.append(f2.result())
			for f1 in future1_list:
				f1.result()

	def trigger_listener(self, listener: EventListener, args: Tuple[Any, ...]) -> 'Future[None]':
		"""
		Event listener triggering entrance which correctly handles sync / async listener callback
		"""
		if listener.is_async():
			coro = self.__trigger_listener_async(listener, args)
			return self.mcdr_server.async_task_executor.submit(coro, plugin=listener.plugin)
		else:
			self.__trigger_listener_sync(listener, args)
			return future_utils.completed(None)

	def __trigger_listener_sync(self, listener: EventListener, args: Tuple[Any, ...]):
		"""
		Event listener triggering implementation (sync)
		The server_interface parameter will be automatically added as the 1st parameter
		"""
		try:
			with self.with_plugin_context(listener.plugin):
				listener.callback(listener.plugin.server_interface, *args)
		except Exception:
			self.logger.exception('Error invoking listener {}'.format(listener))

	async def __trigger_listener_async(self, listener: EventListener, args: Tuple[Any, ...]):
		"""
		Event listener triggering implementation (async)
		The server_interface parameter will be automatically added as the 1st parameter
		"""
		try:
			with self.with_plugin_context(listener.plugin):
				await listener.callback(listener.plugin.server_interface, *args)
		except Exception:
			self.logger.exception('Error invoking async listener {}'.format(listener))
