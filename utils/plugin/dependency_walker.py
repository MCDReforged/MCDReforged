import collections
from typing import Dict, List

from utils.plugin.plugin_manager import PluginManager
from utils.plugin.version import VersionRequirement


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


class VisitingStatus:
	UNVISITED = 0
	PASS = 1
	FAIL = 2


WalkResult = collections.namedtuple('WalkResult', 'plugin_id success reason')


class DependencyWalker:
	def __init__(self, plugin_manager):
		self.plugin_manager = plugin_manager  # type: PluginManager
		self.visiting_status = {}  # type: Dict[str, int]
		self.visiting_plugins = set()
		self.topo_order = []

	def get_visiting_status(self, plugin_id):
		value = self.visiting_status.get(plugin_id)
		if value is None:
			value = VisitingStatus.UNVISITED
			self.visiting_status[plugin_id] = value
		return value

	def ensure_loaded(self, plugin_id: str, requirement: VersionRequirement):
		visiting_status = self.get_visiting_status(plugin_id)
		if visiting_status == VisitingStatus.PASS:
			return
		if visiting_status == VisitingStatus.FAIL:
			raise DependencyParentFail()

		if plugin_id in self.visiting_plugins:
			raise DependencyLoop()

		self.visiting_plugins.add(plugin_id)
		try:
			plugin = self.plugin_manager.plugins.get(plugin_id)
			if plugin is None:
				raise DependencyNotFound()
			if requirement is not None and not requirement.accept(plugin.get_meta_data().version):
				raise DependencyNotMet()

			for dep_id, requirement in plugin.get_meta_data().dependencies.items():
				try:
					self.ensure_loaded(dep_id, requirement)
				except DependencyError:
					self.visiting_status[plugin_id] = VisitingStatus.FAIL
					raise

			self.visiting_status[plugin_id] = VisitingStatus.PASS
			self.topo_order.append(plugin_id)
		finally:
			self.visiting_plugins.remove(plugin_id)

	def walk(self) -> List[WalkResult]:
		self.visiting_status.clear()
		self.visiting_plugins.clear()
		self.topo_order.clear()
		fail_list = []
		for plugin in self.plugin_manager.plugins.values():
			try:
				for dep_id, restriction in plugin.get_meta_data().dependencies.items():
					self.ensure_loaded(dep_id, restriction)
			except DependencyError as e:
				fail_list.append((plugin.get_meta_data().id, e))
		result = []
		for plugin_id, error in fail_list:
			result.append(WalkResult(plugin_id, False, error))
		for plugin_id in self.topo_order:
			result.append(WalkResult(plugin_id, True, None))
		return result
