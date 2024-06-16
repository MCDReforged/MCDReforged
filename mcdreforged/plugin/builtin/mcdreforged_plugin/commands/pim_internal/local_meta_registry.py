import datetime
from typing import Optional, Dict, TYPE_CHECKING

from typing_extensions import override

from mcdreforged.constants.core_constant import DEFAULT_LANGUAGE
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class LocalReleaseData(ReleaseData):
	pass


class LocalMetaRegistry(MetaRegistry):
	def __init__(self, plugin_manager: 'PluginManager', cache: bool = True):
		self.__plugin_manager = plugin_manager
		self.__do_cache = cache
		self.__cached_data: Optional[dict] = None

	@property
	@override
	def plugins(self) -> Dict[str, PluginData]:
		if self.__do_cache and self.__cached_data is not None:
			return self.__cached_data

		result = {}
		for plugin in self.__plugin_manager.get_all_plugins():
			meta = plugin.get_metadata()
			version = str(meta.version)
			if isinstance(meta.description, str):
				description = {DEFAULT_LANGUAGE: meta.description}
			elif isinstance(meta.description, dict):
				description = meta.description.copy()
			else:
				description = {}
			result[meta.id] = PluginData(
				id=meta.id,
				name=meta.name,
				repos_url='*local*',
				repos_owner='*local*',
				repos_name='*local*',
				latest_version=version,
				description=description,
				releases={version: LocalReleaseData(
					version=version,
					tag_name='',
					url='',
					created_at=datetime.datetime.now(),
					dependencies={},
					requirements=[],
					asset_id=0,
					file_name='',
					file_size=0,
					file_url='',
					file_sha256='',
				)}
			)
		if self.__do_cache:
			self.__cached_data = result
		return result
