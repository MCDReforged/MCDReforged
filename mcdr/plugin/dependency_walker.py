import collections
from typing import Dict, List

from mcdr import constant
from mcdr.logger import DebugOption
from mcdr.plugin.version import VersionRequirement


class DependencyError(Exception):
	pass


class DependencyParentFail(DependencyError):
	pass


class DependencyNotFound(DependencyError):
	pass


class DependencyNotMet(DependencyError):
	pass


class DependencyLoop(DependencyError):
	pass


class VisitingState:
	UNVISITED = 0
	PASS = 1
	FAIL = 2


WalkResult = collections.namedtuple('WalkResult', 'plugin_id success reason')


class DependencyWalker:
	def __init__(self, plugin_manager):
		from mcdr.plugin.plugin_manager import PluginManager
		self.plugin_manager = plugin_manager  # type: PluginManager
		self.visiting_state = {}  # type: Dict[str, int]
		self.visiting_plugins = set()
		self.topo_order = []

	def get_visiting_status(self, plugin_id):
		value = self.visiting_state.get(plugin_id)
		if value is None:
			value = VisitingState.UNVISITED
			self.visiting_state[plugin_id] = value
		return value

	def ensure_loaded(self, plugin_id: str, requirement: VersionRequirement or None):
		visiting_status = self.get_visiting_status(plugin_id)
		if visiting_status == VisitingState.PASS:
			return
		if visiting_status == VisitingState.FAIL:
			raise DependencyParentFail('Parent dependency {} failed to check dependency'.format(plugin_id))

		if plugin_id in self.visiting_plugins:
			raise DependencyLoop('Dependency loop at {}'.format(plugin_id))

		self.visiting_plugins.add(plugin_id)
		try:
			if plugin_id == constant.NAME:  # MCDReforged
				plugin_name_display = plugin_id
				plugin_version = constant.VERSION
				plugin_dependencies = {}
			else:
				plugin = self.plugin_manager.plugins.get(plugin_id)
				if plugin is None:
					raise DependencyNotFound('Dependency {} not found'.format(plugin_id))
				plugin_name_display = plugin.get_name()
				plugin_version = plugin.get_meta_data().version
				plugin_dependencies = plugin.get_meta_data().dependencies

			if requirement is not None and isinstance(requirement, VersionRequirement) and not requirement.accept(plugin_version):
				raise DependencyNotMet('Dependency {} does not meet version requirement {}'.format(plugin_name_display, requirement))
			for dep_id, req in plugin_dependencies.items():
				try:
					self.ensure_loaded(dep_id, req)
				except DependencyError as e:
					self.visiting_state[plugin_id] = VisitingState.FAIL
					self.plugin_manager.logger.debug('Set visiting state of {} to FAIL due to "{}"'.format(plugin_id, e), option=DebugOption.PLUGIN)
					raise
			self.topo_order.append(plugin_id)
			self.visiting_state[plugin_id] = VisitingState.PASS
		finally:
			self.visiting_plugins.remove(plugin_id)

	def walk(self) -> List[WalkResult]:
		self.visiting_state.clear()
		self.visiting_plugins.clear()
		self.topo_order.clear()
		fail_list = []
		for plugin in self.plugin_manager.plugins.values():
			try:
				plugin_id = plugin.get_meta_data().id
				if self.get_visiting_status(plugin_id) is not VisitingState.FAIL:
					self.ensure_loaded(plugin_id, None)
				else:
					raise DependencyError('Visiting state of plugin {} is already FAIL'.format(plugin))
			except DependencyError as e:
				fail_list.append((plugin.get_meta_data().id, e))
		result = []
		for plugin_id, error in fail_list:
			result.append(WalkResult(plugin_id, False, error))
		for plugin_id in self.topo_order:
			result.append(WalkResult(plugin_id, True, None))
		return result
