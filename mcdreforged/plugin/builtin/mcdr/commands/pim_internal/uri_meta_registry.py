import datetime
from typing import Dict, Mapping, TYPE_CHECKING

from typing_extensions import override

from mcdreforged.constants.core_constant import DEFAULT_LANGUAGE
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, UriReleaseData

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_install import _UriMetadata


class UriMetaRegistry(MetaRegistry):
	def __init__(self, uri_metadata_map: Dict[str, '_UriMetadata']):
		self.__plugins: Dict[str, PluginData] = {}

		for plugin_id, data in uri_metadata_map.items():
			metadata = data.metadata
			uri = data.uri
			local_path = data.local_path
			requirements = data.requirements
			version = str(metadata.version)

			if isinstance(metadata.description, str):
				description = {DEFAULT_LANGUAGE: metadata.description}
			elif isinstance(metadata.description, dict):
				description = metadata.description.copy()
			else:
				description = {}

			dependencies: Dict[str, str] = {}
			if metadata.dependencies:
				for dep_id, dep_req in metadata.dependencies.items():
					dependencies[dep_id] = dep_req

			release = UriReleaseData(
				version=version,
				tag_name='',
				url='',
				created_at=datetime.datetime.now(),
				dependencies=dependencies,
				requirements=requirements,
				asset_id=0,
				file_name=local_path.name,
				file_size=local_path.stat().st_size,
				file_url='',
				file_sha256='',
				source_uri=uri,
				local_file_path=local_path,
			)

			self.__plugins[plugin_id] = PluginData(
				id=plugin_id,
				name=metadata.name,
				repos_url='*uri*',
				repos_owner='*uri*',
				repos_name='*uri*',
				latest_version=version,
				description=description,
				releases={version: release},
			)

	@property
	@override
	def plugins(self) -> Mapping[str, PluginData]:
		return self.__plugins
