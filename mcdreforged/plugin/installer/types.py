import dataclasses
import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Mapping

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.plugin.meta.version import Version

PluginId = str
PluginResolution = Dict[PluginId, Version]
PackageRequirements = List[str]


@dataclasses.dataclass(frozen=True)
class ReleaseData:
	version: str
	tag_name: str
	url: str
	created_at: datetime.datetime
	dependencies: Dict[PluginId, str]
	requirements: List[str]
	asset_id: int
	file_name: str
	file_size: int
	file_url: str
	file_sha256: str


@dataclasses.dataclass
class PluginData:
	id: PluginId
	name: Optional[str]
	repos_url: str
	repos_owner: str
	repos_name: str
	latest_version: Optional[str]
	description: Dict[str, str]  # lang -> text
	releases: Dict[str, ReleaseData] = dataclasses.field(default_factory=dict)

	def copy(self) -> 'PluginData':
		return PluginData(
			id=self.id,
			name=self.name,
			repos_url=self.repos_url,
			repos_owner=self.repos_owner,
			repos_name=self.repos_name,
			latest_version=self.latest_version,
			description=self.description.copy(),
			releases=self.releases.copy(),
		)

	@property
	def latest_version_parsed(self) -> Optional[Version]:
		if self.latest_version is not None:
			return Version(self.latest_version)
		return None

	@property
	def repos_pair(self) -> str:
		return f'{self.repos_owner}/{self.repos_name}'

	def description_for(self, language: str) -> Optional[str]:
		return self.description.get(language, self.description.get(core_constant.DEFAULT_LANGUAGE))


class MetaRegistry(ABC):
	@property
	@abstractmethod
	def plugins(self) -> Mapping[str, PluginData]:
		raise NotImplementedError()

	def __getitem__(self, plugin_id: str) -> PluginData:
		return self.plugins[plugin_id]

	def __contains__(self, plugin_id: str) -> bool:
		return plugin_id in self.plugins

	def __len__(self) -> int:
		return len(self.plugins)


class EmptyMetaRegistry(MetaRegistry):
	@property
	@override
	def plugins(self) -> Mapping[str, PluginData]:
		return {}


class MergedMetaRegistry(MetaRegistry):
	def __init__(self, *sources: MetaRegistry):
		self.__plugins: Dict[str, PluginData] = {}
		for source in sources:
			for plugin_id, plugin_data in source.plugins.items():
				if plugin_id not in self.__plugins:
					self.__plugins[plugin_id] = plugin_data.copy()
				else:
					existing = self.__plugins[plugin_id]
					existing.releases.update(plugin_data.releases)
					if existing.latest_version is None:
						existing.latest_version = plugin_data.latest_version
						existing.description = plugin_data.description
					elif plugin_data.latest_version is not None:
						if Version(existing.latest_version) < Version(plugin_data.latest_version):
							existing.latest_version = plugin_data.latest_version
							existing.description = plugin_data.description

	@property
	@override
	def plugins(self) -> Mapping[str, PluginData]:
		return self.__plugins
