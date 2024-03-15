import gzip
import json
import lzma
import threading
from typing import Optional, Dict

from typing_extensions import override

from mcdreforged.plugin.installer.types import MetaCache, PluginData, ReleaseData
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils import request_util


class CatalogueMetaCache(MetaCache):
	def __init__(self, plugin: Dict[str, PluginData]):
		self.__plugins = plugin

	@override
	@property
	def plugins(self) -> Dict[str, PluginData]:
		return self.__plugins


class MetaHolder:
	def __init__(self):
		self.__meta_cache: Optional[MetaCache] = None
		self.__meta_cache_lock = threading.Lock()

	def get(self) -> MetaCache:
		# TODO cache TTL
		if self.__meta_cache is not None:
			return self.__meta_cache
		with self.__meta_cache_lock:
			if self.__meta_cache is not None:
				return self.__meta_cache

			meta_json = self._get_meta_json()
			self.__meta_cache = self.__load_meta_json(meta_json)
			return self.__meta_cache

	def _get_meta_json(self) -> dict:
		url = 'https://meta.mcdreforged.com/everything_slim.json.xz'
		max_size = 20 * 2 ** 20  # 20MiB limit. In 2024-03-14, the size is only 545KiB

		buf = request_util.get(url, timeout=10, max_size=max_size)

		decompressor = lzma.LZMADecompressor()
		content = decompressor.decompress(buf, max_size + 1)
		if len(content) > max_size:
			raise ValueError('content too large {} {}'.format(len(content), max_size))

		return json.loads(content.decode('utf8'))

	@classmethod
	def __load_meta_json(cls, meta_json: dict) -> MetaCache:
		plugins = {}

		for plugin_id, aop in meta_json.get('plugins', {}).items():
			if aop.get('release') is None or aop.get('meta') is None:
				continue
			if (idx := aop['release'].get('latest_version_index')) is not None:
				meta = aop['release']['releases'][idx]['meta']
				latest_version = meta['version']
			else:
				meta = aop['meta']
				latest_version = None

			plugin_data = PluginData(
				id=plugin_id,
				name=meta.get('name'),
				latest_version=latest_version,
				description=meta.get('description', {}),
			)
			for release in aop['release']['releases']:
				meta = release['meta']
				asset = release['asset']
				release_data = ReleaseData(
					version=meta['version'],
					dependencies=meta.get('dependencies', {}),
					requirements=meta.get('requirements', []),
					file_name=asset['name'],
					file_size=asset['size'],
					file_url=asset['browser_download_url'],
					file_sha256=asset['hash_sha256'],
				)
				Version(release_data.version)
				plugin_data.releases[release_data.version] = release_data
			plugins[plugin_id] = plugin_data

		return CatalogueMetaCache(plugins)

	def get_release(self, plugin_id: str, version: str) -> ReleaseData:
		return self.get().plugins[plugin_id].releases[version]


class PersistMetaHolder(MetaHolder):
	def __init__(self, cache_file: str):
		super().__init__()
		self.cache_file = cache_file

	def _get_meta_json(self) -> dict:
		try:
			with gzip.open(self.cache_file, 'rt', encoding='utf8') as f:
				return json.load(f)
		except (OSError, ValueError):
			pass

		meta = super()._get_meta_json()
		with gzip.open(self.cache_file, 'wt', encoding='utf8') as f:
			json.dump(meta, f)
		return meta
