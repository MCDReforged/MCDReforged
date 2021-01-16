import collections
from enum import unique, Enum, auto
from typing import Dict, List, TYPE_CHECKING, Tuple

from mcdreforged.plugin.meta.version import VersionRequirement
from mcdreforged.utils.logger import DebugOption

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


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


@unique
class VisitingState(Enum):
	UNVISITED = auto()
	PASS = auto()
	FAIL = auto()


WalkResult = collections.namedtuple('WalkResult', 'plugin_id success reason')


class DependencyWalker:
	def __init__(self, plugin_manager: 'PluginManager'):
		self.plugin_manager = plugin_manager
		self.tr = plugin_manager.mcdr_server.tr
		self.visiting_state = {}  # type: Dict[str, VisitingState]
		self.visiting_plugins = set()
		self.visiting_plugin_stack = []
		self.topo_order = []

	def get_visiting_status(self, plugin_id):
		value = self.visiting_state.get(plugin_id)
		if value is None:
			value = VisitingState.UNVISITED
			self.visiting_state[plugin_id] = value
		return value

	def ensure_loaded(self, plugin_id: str, requirement: VersionRequirement or None):
		visiting_status = self.get_visiting_status(plugin_id)
		if visiting_status == VisitingState.FAIL:
			raise DependencyParentFail(self.tr('dependency_walker.dependency_parent_failed', plugin_id))

		if plugin_id in self.visiting_plugins:
			start = 0
			for i, pid in enumerate(self.visiting_plugin_stack):
				if pid == plugin_id:
					start = i
					break
			loop_list = self.visiting_plugin_stack[start:]
			loop_list.append(plugin_id)
			loop_message = ' -> '.join(loop_list)
			raise DependencyLoop(self.tr('dependency_walker.dependency_loop', plugin_id, loop_message))

		self.visiting_plugins.add(plugin_id)
		self.visiting_plugin_stack.append(plugin_id)
		try:
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			if plugin is None:
				raise DependencyNotFound(self.tr('dependency_walker.dependency_not_found', plugin_id))
			plugin_name_display = plugin.get_name()
			plugin_version = plugin.get_metadata().version
			plugin_dependencies = plugin.get_metadata().dependencies

			if requirement is not None and isinstance(requirement, VersionRequirement) and not requirement.accept(plugin_version):
				raise DependencyNotMet(self.tr('dependency_walker.dependency_not_met', plugin_name_display, requirement))

			if visiting_status == VisitingState.PASS:  # no need to do further dependencies check, already done
				return

			for dep_id, req in plugin_dependencies.items():
				try:
					self.ensure_loaded(dep_id, req)
				except DependencyError as e:
					self.visiting_state[plugin_id] = VisitingState.FAIL
					self.plugin_manager.logger.debug('Set visiting state of {} to FAIL due to "{}"'.format(plugin_id, e), option=DebugOption.PLUGIN)
					raise
			if not plugin.is_permanent():
				self.topo_order.append(plugin_id)
			self.visiting_state[plugin_id] = VisitingState.PASS
		finally:
			self.visiting_plugins.remove(plugin_id)
			self.visiting_plugin_stack.pop(len(self.visiting_plugin_stack) - 1)

	def walk(self) -> List[WalkResult]:
		self.visiting_state.clear()
		self.visiting_plugins.clear()
		self.visiting_plugin_stack.clear()
		self.topo_order.clear()
		fail_list = []  # type: List[Tuple[str, DependencyError]]
		for plugin in self.plugin_manager.get_regular_plugins():
			try:
				plugin_id = plugin.get_id()
				visiting_state = self.get_visiting_status(plugin_id)
				if visiting_state is not VisitingState.FAIL:
					self.ensure_loaded(plugin_id, None)
				else:
					raise DependencyError(self.tr('dependency_walker.dependency_already_failed', plugin, visiting_state))
			except DependencyError as e:
				fail_list.append((plugin.get_id(), e))
		result = []
		for plugin_id, error in fail_list:
			result.append(WalkResult(plugin_id, False, error))
		for plugin_id in self.topo_order:
			result.append(WalkResult(plugin_id, True, None))
		return result
