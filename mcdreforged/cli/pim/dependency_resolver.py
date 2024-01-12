import re
import subprocess
import traceback
from typing import List, Dict, NamedTuple, Union, Mapping, Iterator, Iterable, Sequence, Set

import resolvelib
from resolvelib.resolvers import RequirementInformation

import sys
from mcdreforged.plugin.meta.version import VersionRequirement, Version

PluginId = str
PluginResolution = Dict[PluginId, Version]


class PluginRequirement(NamedTuple):
	id: PluginId
	requirement: VersionRequirement

	@classmethod
	def of(cls, req_str: str) -> 'PluginRequirement':
		matched = re.match(r'^[a-zA-Z0-9_]{1,64}', req_str)
		if matched is None:
			raise ValueError('bad plugin requirement {}'.format(repr(req_str)))
		plugin_id = matched.group(0)
		requirement = VersionRequirement(req_str[len(plugin_id):])
		return PluginRequirement(plugin_id, requirement)


class PluginCandidate(NamedTuple):
	id: PluginId
	version: Version


class PluginVersionInfo(NamedTuple):
	version: Version
	plugin_requirements: Dict[PluginId, VersionRequirement]
	package_requirements: List[str]


class PluginMeta(NamedTuple):
	id: PluginId
	versions: Dict[Version, PluginVersionInfo]  # order: new -> old

	@classmethod
	def of(cls, plugin_id: str, plugin_version_str: str) -> 'PluginMeta':
		version = Version(plugin_version_str)
		return PluginMeta(plugin_id, {version: PluginVersionInfo(version, {}, [])})

	@classmethod
	def of_metadata(cls, plugin_metadata: dict) -> 'PluginMeta':
		return cls.of(plugin_metadata['id'], plugin_metadata['version'])


PluginMetas = Dict[PluginId, PluginMeta]
KT = PluginId  # Identifier
RT = PluginRequirement  # Requirement
CT = PluginCandidate  # Candidate


class MyProvider(resolvelib.AbstractProvider):
	def __init__(self, plugin_metas: PluginMetas):
		self.plugin_metas = plugin_metas.copy()

	def identify(self, requirement_or_candidate: Union[RT, CT]) -> KT:
		return requirement_or_candidate.id

	def get_preference(
			self,
			identifier: KT,
			resolutions: Mapping[KT, CT],
			candidates: Mapping[KT, Iterator[CT]],
			information: Mapping[KT, Iterator[RequirementInformation[RT, CT]]],
			backtrack_causes: Sequence[RequirementInformation[RT, CT]],
	):
		return 0

	def find_matches(
			self,
			identifier: KT,
			requirements: Mapping[KT, Iterator[RT]],
			incompatibilities: Mapping[KT, Iterator[CT]],
	):
		meta = self.plugin_metas.get(identifier)
		if meta is None:
			return []

		bad_versions = {c.version for c in incompatibilities.get(identifier, [])}
		candidates = []
		for version, pvi in meta.versions.items():
			if all(r.requirement.accept(version) for r in requirements.get(identifier, [])) and version not in bad_versions:
				candidates.append(PluginCandidate(identifier, version))

		candidates.sort(key=lambda c: c.version, reverse=True)
		return candidates

	def is_satisfied_by(self, requirement: RT, candidate: CT) -> bool:
		return requirement.id == candidate.id and requirement.requirement.accept(candidate.version)

	def get_dependencies(self, candidate: CT) -> Iterable[RT]:
		dependencies = []
		for pid, req in self.plugin_metas[candidate.id].versions[candidate.version].plugin_requirements.items():
			dependencies.append(PluginRequirement(pid, req))
		return dependencies


def pip_check(package_requirements: List[str]) -> bool:
	if len(package_requirements) == 0:
		return True
	cmd = [
		sys.executable,
		'-m', 'pip', 'install',
		'--dry-run',
		'--report', '-',
		'--quiet',
	]
	cmd.extend(package_requirements)
	try:
		output = subprocess.check_output(cmd)
	except subprocess.CalledProcessError as e:
		return False
	return True


class DependencyResolver:
	def __init__(self, cata_meta: dict, existing_plugins: PluginResolution):
		self.plugin_metas = {}

		from mcdreforged.plugin.builtin.mcdreforged_plugin import mcdreforged_plugin
		from mcdreforged.plugin.builtin import python_plugin
		permanent_plugin_meta = [
			PluginMeta.of_metadata(mcdreforged_plugin.METADATA),
			PluginMeta.of_metadata(python_plugin.METADATA),
		]
		self.__permanent_plugin_ids: Set[PluginId] = set()
		for meta in permanent_plugin_meta:
			self.__permanent_plugin_ids.add(meta.id)
			self.plugin_metas[meta.id] = meta

		self.existing_plugins = existing_plugins
		for plugin_id, meta_all in cata_meta['plugins'].items():
			meta = PluginMeta(id=plugin_id, versions={})
			for release in meta_all['release']['releases']:
				if isinstance(release['meta'], dict):
					try:
						version = release['meta']['version']
						meta.versions[Version(version)] = PluginVersionInfo(
							version=version,
							plugin_requirements={pid: VersionRequirement(vr) for pid, vr in release['meta']['dependencies'].items()},
							package_requirements=release['meta']['requirements'],
						)
					except ValueError:
						# TODO: better handling
						traceback.print_exc()
			self.plugin_metas[plugin_id] = meta

	def resolve(self, requirements: List[PluginRequirement]) -> PluginResolution:
		provider = MyProvider(self.plugin_metas)
		reporter = resolvelib.BaseReporter()
		resolver = resolvelib.Resolver(provider, reporter)

		try:
			result = resolver.resolve(requirements, max_rounds=10000)
		except resolvelib.ResolutionError as e:
			traceback.print_exc()
			raise
		else:
			print('ok')
			resolution = {}
			for pid, pc in result.mapping.items():
				if pid not in self.__permanent_plugin_ids:
					resolution[pid] = pc.version
					print(pid, pc.version)

			print()
			for u, v in result.graph.iter_edges():
				print(u, v)
			print()
			for k, v in result.criteria.items():
				print(k, v)
			return resolution

	def execute(self):
		pass
