import collections
import dataclasses
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Mapping

from typing_extensions import override

from mcdreforged.plugin.meta.version import Version

PluginId = str
PluginResolution = Dict[PluginId, Version]
PackageResolution = List[str]


# =================== For Meta Parsing ===================


@dataclasses.dataclass(frozen=True)
class ReleaseData:
	version: str
	dependencies: Dict[PluginId, str]
	requirements: List[str]
	file_name: str
	file_size: int
	file_url: str
	file_sha256: str


@dataclasses.dataclass(frozen=True)
class PluginData:
	id: PluginId
	name: Optional[str]
	latest_version: Optional[str]
	description: Dict[str, str]  # lang -> text
	releases: Dict[str, ReleaseData] = dataclasses.field(default_factory=dict)


class MetaCache(ABC):
	@property
	@abstractmethod
	def plugins(self) -> Mapping[str, PluginData]:
		raise NotImplementedError()

	def __getitem__(self, plugin_id: str) -> PluginData:
		return self.plugins[plugin_id]


class ChainMetaCache(MetaCache):
	def __init__(self, *sources: MetaCache):
		self.__sources = sources

	@override
	@property
	def plugins(self) -> Mapping[str, PluginData]:
		return collections.ChainMap(*[m.plugins for m in self.__sources])
