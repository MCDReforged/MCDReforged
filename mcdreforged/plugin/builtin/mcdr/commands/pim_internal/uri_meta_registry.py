import dataclasses
import datetime
from pathlib import Path
from typing import Dict, Mapping, Optional

from typing_extensions import override

from mcdreforged.constants.core_constant import DEFAULT_LANGUAGE
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.uri_plugin_prepare_helper import PreparedUriPlugin
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData
from mcdreforged.plugin.meta.version import Version


@dataclasses.dataclass(frozen=True)
class UriReleaseData(ReleaseData):
	source_uri: str
	local_file_path: Path


class UriMetaRegistry(MetaRegistry):
	def __init__(self, uri_plugins: Dict[str, PreparedUriPlugin], base_registry: Optional[MetaRegistry] = None):
		self.__plugins: Dict[str, PluginData] = {}

		for plugin_id, data in uri_plugins.items():
			metadata = data.metadata
			version = str(metadata.version)

			if isinstance(metadata.description, str):
				description = {DEFAULT_LANGUAGE: metadata.description}
			elif isinstance(metadata.description, dict):
				description = metadata.description.copy()
			else:
				description = {}

			release = UriReleaseData(
				version=version,
				tag_name='',
				url='',
				created_at=datetime.datetime.now(),
				dependencies={dep_id: str(dep_req) for dep_id, dep_req in metadata.dependencies.items()},
				requirements=data.requirements,
				asset_id=0,
				file_name=data.file_name,
				file_size=data.file_size,
				file_url='',
				file_sha256=data.file_sha256,
				source_uri=data.specifier.uri,
				local_file_path=data.local_path,
			)
			releases: Dict[str, ReleaseData] = {version: release}
			if base_registry is not None and plugin_id in base_registry:
				# Overlay equivalent version spellings with the same URI artifact
				# and dependencies; leave unrelated catalogue/local versions intact.
				for existing_version in base_registry[plugin_id].releases:
					parsed_version = Version(existing_version)
					if parsed_version == metadata.version:
						releases[existing_version] = release
						releases[str(parsed_version)] = release

			self.__plugins[plugin_id] = PluginData(
				id=plugin_id,
				name=metadata.name,
				repos_url='*uri*',
				repos_owner='*uri*',
				repos_name='*uri*',
				latest_version=version,
				description=description,
				releases=releases,
			)

	@property
	@override
	def plugins(self) -> Mapping[str, PluginData]:
		return self.__plugins
