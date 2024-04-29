import dataclasses
import re
import subprocess
from typing import List, Union, Mapping, Iterator, Iterable, Sequence, Optional, Dict

import resolvelib
from resolvelib.resolvers import RequirementInformation
from typing_extensions import override

import sys
from mcdreforged.plugin.installer.meta_holder import MetaRegistry
from mcdreforged.plugin.installer.types import PluginId, PluginResolution, PackageRequirements
from mcdreforged.plugin.meta.version import VersionRequirement, Version


@dataclasses.dataclass(frozen=True)
class PluginRequirement:
	id: PluginId
	requirement: VersionRequirement
	preferred_version: Optional[Version] = None

	@classmethod
	def of(cls, req_str: str) -> 'PluginRequirement':
		matched = re.match(r'^[a-z0-9_]{1,64}', req_str)
		if matched is None:
			raise ValueError('bad plugin requirement {}'.format(repr(req_str)))
		plugin_id = matched.group(0)
		requirement = VersionRequirement(req_str[len(plugin_id):])
		return PluginRequirement(plugin_id, requirement)

	def __str__(self):
		return '{}{}'.format(self.id, self.requirement)


@dataclasses.dataclass(frozen=True)
class PluginCandidate:
	id: PluginId
	version: Version

	def __str__(self):
		return '{}@{}'.format(self.id, self.version)


@dataclasses.dataclass(frozen=True)
class PluginVersionInfo:
	version: Version
	plugin_requirements: Dict[PluginId, VersionRequirement]
	package_requirements: PackageRequirements


@dataclasses.dataclass(frozen=True)
class PluginMeta:
	id: PluginId
	versions: Dict[Version, PluginVersionInfo]  # order: new -> old

	@classmethod
	def of(cls, plugin_id: str, plugin_version_str: str) -> 'PluginMeta':
		version = Version(plugin_version_str)
		return PluginMeta(plugin_id, {version: PluginVersionInfo(version, {}, [])})

	@classmethod
	def of_metadata(cls, plugin_metadata: dict) -> 'PluginMeta':
		return cls.of(plugin_metadata['id'], plugin_metadata['version'])

	@classmethod
	def builtin_plugin_metadata_list(cls) -> List['PluginMeta']:
		from mcdreforged.plugin.builtin.mcdreforged_plugin import mcdreforged_plugin
		from mcdreforged.plugin.builtin import python_plugin
		return [
			PluginMeta.of_metadata(mcdreforged_plugin.METADATA),
			PluginMeta.of_metadata(python_plugin.METADATA),
		]


PluginMetas = Dict[PluginId, PluginMeta]
KT = PluginId  # Identifier
RT = PluginRequirement  # Requirement
CT = PluginCandidate  # Candidate


class PluginMetaProvider(resolvelib.AbstractProvider):
	def __init__(self, plugin_metas: PluginMetas):
		self.plugin_metas = plugin_metas.copy()

	@override
	def identify(self, requirement_or_candidate: Union[RT, CT]) -> KT:
		return requirement_or_candidate.id

	@override
	def get_preference(
			self,
			identifier: KT,
			resolutions: Mapping[KT, CT],
			candidates: Mapping[KT, Iterator[CT]],
			information: Mapping[KT, Iterator['RequirementInformation[RT, CT]']],
			backtrack_causes: Sequence['RequirementInformation[RT, CT]'],
	):
		return 0

	@override
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
		reqs: List[RT] = list(requirements.get(identifier, []))
		candidates: List[CT] = []
		for version, pvi in meta.versions.items():
			def check() -> bool:
				if version in bad_versions:
					return False
				for r in reqs:
					if not r.requirement.accept(version):
						return False
				return True

			if check():
				candidates.append(PluginCandidate(identifier, version))

		preferred_versions = {r.preferred_version for r in reqs if r.preferred_version is not None}
		candidates.sort(key=lambda c: (c.version in preferred_versions, c.version), reverse=True)
		return candidates

	@override
	def is_satisfied_by(self, requirement: RT, candidate: CT) -> bool:
		return requirement.id == candidate.id and requirement.requirement.accept(candidate.version)

	@override
	def get_dependencies(self, candidate: CT) -> Iterable[RT]:
		dependencies = []
		for pid, req in self.plugin_metas[candidate.id].versions[candidate.version].plugin_requirements.items():
			dependencies.append(PluginRequirement(pid, req))
		return dependencies


class PluginDependencyResolver:
	def __init__(self, meta_cache: MetaRegistry):
		self.__plugin_metas: PluginMetas = {}
		for plugin_id, plugin in meta_cache.plugins.items():
			meta = PluginMeta(id=plugin_id, versions={})
			for version_str, release in plugin.releases.items():
				version = Version(version_str)
				meta.versions[version] = PluginVersionInfo(
					version=version,
					plugin_requirements={pid: VersionRequirement(vr) for pid, vr in release.dependencies.items()},
					package_requirements=release.requirements,
				)
			self.__plugin_metas[plugin_id] = meta

	def resolve(self, requirements: Iterable[PluginRequirement], reporter: Optional[resolvelib.BaseReporter] = None) -> Union[PluginResolution, resolvelib.ResolutionError]:
		if reporter is None:
			reporter = resolvelib.BaseReporter()
		provider = PluginMetaProvider(self.__plugin_metas)
		resolver = resolvelib.Resolver(provider, reporter)

		try:
			result = resolver.resolve(requirements, max_rounds=10000)
		except resolvelib.ResolutionError as e:
			return e

		resolution: PluginResolution = {}
		for pid, pc in result.mapping.items():
			resolution[pid] = pc.version

		return resolution


class PackageRequirementResolver:
	def __init__(self, package_requirements: PackageRequirements):
		self.package_requirements = package_requirements

	def check(self, *, extra_args: Iterable[str] = ()) -> Union[Optional[str], subprocess.CalledProcessError]:
		if len(self.package_requirements) == 0:
			return None
		cmd = [
			sys.executable,
			'-X', 'utf8',
			'-m', 'pip', 'install',
			'--dry-run',
			'--disable-pip-version-check',
			*extra_args,
			*self.package_requirements,
		]
		try:
			return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode('utf8')
		except subprocess.CalledProcessError as e:
			return e

	def install(self, *, extra_args: Iterable[str] = ()):
		if len(self.package_requirements) == 0:
			return
		cmd = [
			sys.executable,
			'-m', 'pip', 'install',
			'--disable-pip-version-check',
			*extra_args,
			*self.package_requirements
		]
		subprocess.check_call(cmd)
