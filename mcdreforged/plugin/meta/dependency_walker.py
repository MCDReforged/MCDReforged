from contextlib import contextmanager
from enum import unique, Enum, auto
from typing import Dict, List, TYPE_CHECKING, NamedTuple, Optional, Set, TypeVar, Generic

from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.plugin.meta.version import VersionRequirement

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


T = TypeVar('T')


class LoopChecker(Generic[T]):
	def __init__(self):
		self.__elements: Set[T] = set()
		self.__stack: List[T] = []

	@contextmanager
	def enter(self, element: T):
		self.__elements.add(element)
		self.__stack.append(element)
		try:
			yield
		finally:
			self.__elements.remove(element)
			self.__stack.pop(len(self.__stack) - 1)

	def check(self, element: T) -> Optional[List[T]]:
		if element in self.__elements:
			start = 0
			for i, pid in enumerate(self.__stack):
				if pid == element:
					start = i
					break
			loop_list = self.__stack[start:]
			loop_list.append(element)
			return loop_list
		return None


@unique
class VisitingState(Enum):
	UNVISITED = auto()
	PASS = auto()
	FAIL = auto()


class DependencyGraphNode:
	def __init__(self, plugin_id: str):
		self.plugin_id = plugin_id
		self.parents: List['DependencyGraphNode'] = []
		self.children: List['DependencyGraphNode'] = []


class PluginHolder:
	def __init__(self, plugin_id: str):
		self.plugin_id = plugin_id
		self.state = VisitingState.UNVISITED
		self.graph_node: DependencyGraphNode = DependencyGraphNode(plugin_id)
		self.topo_order: int = -1
		self.error: Optional[DependencyError] = None

	def __lt__(self, other: 'PluginHolder') -> bool:
		return (self.topo_order, self.plugin_id) < (other.topo_order, other.plugin_id)


class WalkResult(NamedTuple):
	plugin_id: str
	success: bool
	reason: Optional[DependencyError]


class DependencyWalker:
	def __init__(self, plugin_manager: 'PluginManager'):
		self.__plugin_manager = plugin_manager
		self.__tr = plugin_manager.mcdr_server.create_internal_translator('dependency_walker').tr
		self.__holders: Dict[str, PluginHolder] = {}
		self.__loop_checker: LoopChecker[str] = LoopChecker()
		self.__topo_order: List[str] = []
		self.__walked = False
		self.__walk_plugin_ids: Set[str] = set()

	def __get_holder(self, plugin_id: str) -> PluginHolder:
		holder = self.__holders.get(plugin_id)
		if holder is None:
			holder = PluginHolder(plugin_id)
			self.__holders[plugin_id] = holder
		return holder

	def __add_edge(self, parent_id: str, child_id: str):
		parent = self.__get_holder(parent_id).graph_node
		child = self.__get_holder(child_id).graph_node
		parent.children.append(child)
		child.parents.append(parent)

	def __ensure_loaded(self, plugin_id: str, requirement: Optional[VersionRequirement]):
		holder = self.__get_holder(plugin_id)
		if holder.state == VisitingState.FAIL:
			raise DependencyParentFail(self.__tr('dependency_parent_failed', plugin_id))

		loop_list = self.__loop_checker.check(plugin_id)
		if loop_list is not None:
			loop_message = ' -> '.join(loop_list)
			raise DependencyLoop(self.__tr('dependency_loop', plugin_id, loop_message))

		with self.__loop_checker.enter(plugin_id):
			plugin = self.__plugin_manager.get_plugin_from_id(plugin_id)
			if plugin is None:
				raise DependencyNotFound(self.__tr('dependency_not_found', plugin_id))
			plugin_name_display = plugin.get_name()
			plugin_version = plugin.get_version()
			plugin_dependencies = plugin.get_metadata().dependencies

			if requirement is not None and isinstance(requirement, VersionRequirement) and not requirement.accept(plugin_version):
				raise DependencyNotMet(self.__tr('dependency_not_met', plugin_name_display, requirement))

			if holder.state == VisitingState.PASS:  # no need to do further dependencies check, already done
				return

			for dep_id, req in plugin_dependencies.items():
				self.__add_edge(dep_id, plugin_id)
			for dep_id, req in plugin_dependencies.items():
				try:
					self.__ensure_loaded(dep_id, req)
				except DependencyError as e:
					holder.state = VisitingState.FAIL
					self.__plugin_manager.logger.mdebug('Set visiting state of {} to FAIL due to "{}"'.format(plugin_id, e), option=DebugOption.PLUGIN)
					raise
			if not plugin.is_builtin():
				holder.topo_order = len(self.__topo_order)
				self.__topo_order.append(plugin_id)
			holder.state = VisitingState.PASS

	def walk(self) -> List[WalkResult]:
		if self.__walked:
			raise RuntimeError('Double walk not supported')
		self.__walked = True

		plugin_ids: List[str] = []
		for plugin in self.__plugin_manager.get_regular_plugins():
			plugin_id = plugin.get_id()
			plugin_ids.append(plugin_id)
			self.__walk_plugin_ids.add(plugin_id)

		for plugin_id in plugin_ids:
			holder = self.__get_holder(plugin_id)
			try:
				if holder.state is not VisitingState.FAIL:
					self.__ensure_loaded(plugin_id, None)
				else:
					raise DependencyError(self.__tr('dependency_already_failed', plugin_id, holder.state))
			except DependencyError as e:
				holder.error = e

		result: List[WalkResult] = []
		no_error_ids: Set[str] = set()
		for plugin_id in plugin_ids:
			holder = self.__get_holder(plugin_id)
			if holder.error is None:
				assert holder.state == VisitingState.PASS
				no_error_ids.add(plugin_id)
			else:
				result.append(WalkResult(plugin_id, False, holder.error))
		assert no_error_ids == set(self.__topo_order), 'Unequal success list: {} {}'.format(no_error_ids, self.__topo_order)
		for plugin_id in self.__topo_order:
			result.append(WalkResult(plugin_id, True, None))

		return result

	def __holder_or_raise(self, plugin_id: str) -> PluginHolder:
		if not self.__walked:
			raise RuntimeError("Haven't walked yet")
		if plugin_id not in self.__walk_plugin_ids:
			raise KeyError('Given plugin {} is not in walk target'.format(plugin_id))
		holder = self.__get_holder(plugin_id)
		if holder.error is not None:
			raise holder.error
		return holder

	def get_topo_order(self, plugin_id: str) -> int:
		return self.__holder_or_raise(plugin_id).topo_order

	def get_children(self, plugin_id: str) -> List[str]:
		"""
		:return plugin id list in topo-order, i.e. parent first.
			Result includes the queried plugin itself
		"""
		holder = self.__holder_or_raise(plugin_id)

		def search(node: DependencyGraphNode) -> List[DependencyGraphNode]:
			get_children = [node]
			for child_node in node.children:
				get_children.extend(search(child_node))
			return get_children

		return [
			h.plugin_id
			for h in sorted([
				self.__get_holder(node.plugin_id)
				for node in search(holder.graph_node)
			])
			if h.plugin_id in self.__walk_plugin_ids
		]
