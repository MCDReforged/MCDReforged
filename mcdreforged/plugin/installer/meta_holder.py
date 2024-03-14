import gzip
import json
import lzma
import threading
from typing import Optional, Dict, List

from mcdreforged.utils import request_util
from mcdreforged.utils.serializer import Serializable


class ReleaseData(Serializable):
	version: str
	dependencies: Dict[str, str]
	requirements: List[str]
	file_name: str
	file_size: int
	file_url: str
	file_sha256: str


class PluginData(Serializable):
	id: str
	name: Optional[str]
	latest_version: Optional[str]
	description: Dict[str, str]
	releases: Dict[str, ReleaseData]


class MetaCache(Serializable):
	plugins: Dict[str, PluginData]


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
			self.__meta_cache = self._load_meta_json(meta_json)
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
	def _load_meta_json(cls, meta_json: dict) -> MetaCache:
		cache = MetaCache()
		cache.plugins = {}

		for plugin_id, aop in meta_json.get('plugins', {}).items():
			if aop.get('release') is None or aop.get('meta') is None:
				continue
			if (idx := aop['release'].get('latest_version_index')) is not None:
				release = aop['release']['releases'][idx]
				meta = release['meta']
			else:
				release = None
				meta = aop['meta']

			plugin_data = PluginData()
			plugin_data.id = plugin_id
			plugin_data.name = meta.get('name')
			plugin_data.latest_version = release['meta']['version'] if release is not None else None
			plugin_data.description = meta.get('description', {})
			plugin_data.releases = {}
			for release in aop['release']['releases']:
				meta = release['meta']
				asset = release['asset']
				release_data = ReleaseData()
				release_data.version = meta['version']
				release_data.dependencies = meta.get('dependencies', {})
				release_data.requirements = meta.get('requirements', [])
				release_data.file_name = asset['name']
				release_data.file_size = asset['size']
				release_data.file_url = asset['browser_download_url']
				release_data.file_sha256 = asset['hash_sha256']
				plugin_data.releases[release_data.version] = release_data
			cache.plugins[plugin_id] = plugin_data

		return cache

	def get_release(self, plugin_id: str, version: str) -> ReleaseData:
		return self.get().plugins[plugin_id].releases[version]


class CachedMetaHolder(MetaHolder):
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
