import json
import logging
import lzma
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Callable, Any

from typing_extensions import override

from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData, EmptyMetaRegistry
from mcdreforged.utils import request_util


class CatalogueMetaRegistry(MetaRegistry):
	def __init__(self, plugin: Dict[str, PluginData]):
		self.__plugins = plugin

	@property
	@override
	def plugins(self) -> Dict[str, PluginData]:
		return self.__plugins


class CatalogueMetaRegistryHolder:
	def get_registry(self) -> MetaRegistry:
		meta_json = self._get_meta_json()
		return self._load_meta_json(meta_json)

	@classmethod
	def _get_meta_json(cls) -> dict:
		url = 'https://meta.mcdreforged.com/everything_slim.json.xz'
		max_size = 20 * 2 ** 20  # 20MiB limit. In 2024-03-14, the size is only 545KiB

		buf = request_util.get(url, 'MetaFetcher', timeout=10, max_size=max_size)

		decompressor = lzma.LZMADecompressor()
		content = decompressor.decompress(buf, max_size + 1)
		if len(content) > max_size:
			raise ValueError('content too large {} {}'.format(len(content), max_size))

		return json.loads(content.decode('utf8'))

	@classmethod
	def _load_meta_json(cls, meta_json: dict) -> MetaRegistry:
		plugins = {}

		aop: dict
		for plugin_id, aop in meta_json.get('plugins', {}).items():
			release_summary: dict
			if (release_summary := aop.get('release')) is None or aop.get('meta') is None:
				continue
			if (idx := release_summary.get('latest_version_index')) is not None:
				meta = release_summary['releases'][idx]['meta']
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
			for release in release_summary['releases']:
				meta: dict = release['meta']
				asset: dict = release['asset']
				release_data = ReleaseData(
					version=meta['version'],
					dependencies=meta.get('dependencies', {}),
					requirements=meta.get('requirements', []),
					file_name=asset['name'],
					file_size=asset['size'],
					file_url=asset['browser_download_url'],
					file_sha256=asset['hash_sha256'],
				)
				# verify it
				from mcdreforged.plugin.meta.version import Version
				Version(release_data.version)

				plugin_data.releases[release_data.version] = release_data
			plugins[plugin_id] = plugin_data

		return CatalogueMetaRegistry(plugins)

	def get_release(self, plugin_id: str, version: str) -> ReleaseData:
		return self.get_registry().plugins[plugin_id].releases[version]


class AsyncPersistCatalogueMetaRegistryHolder(CatalogueMetaRegistryHolder):
	CACHE_TTL = 60 * 60

	def __init__(self, logger: logging.Logger, cache_path: Path):
		self.logger = logger
		self.cache_path = cache_path
		self.__meta_lock = threading.Lock()
		self.__meta: MetaRegistry = EmptyMetaRegistry()
		self.__meta_fetch_time: float = 0
		self.__fetch_thread: Optional[threading.Thread] = None
		self.__fetch_thread_lock = threading.Lock()

	@override
	def get_registry(self, *, fetch_callback: Optional[Callable[[], Any]] = None) -> MetaRegistry:
		if self.async_fetch():
			if fetch_callback is not None:
				fetch_callback()
		return self.__meta

	def __load(self):
		if not self.cache_path.is_file():
			return
		try:
			with lzma.open(self.cache_path, 'rt', encoding='utf8') as f:
				data = json.load(f)
			meta = self._load_meta_json(data['meta'])
		except (KeyError, ValueError, OSError):
			self.logger.exception('Failed to load cached meta from {}'.format(self.cache_path))
			return
		with self.__meta_lock:
			self.__meta = meta
			self.__meta_fetch_time = data.get('timestamp', 0)

	def __save(self, meta_json: dict, timestamp: float):
		data = {
			'timestamp': timestamp,
			'meta': meta_json,
		}
		self.cache_path.parent.mkdir(parents=True, exist_ok=True)
		with lzma.open(self.cache_path, 'wt', encoding='utf8') as f:
			json.dump(data, f)

	def init(self):
		try:
			if self.__load():
				self.logger.info('Catalogue meta registry loaded from file')
		except Exception as e:
			self.logger.exception('Catalogue meta registry load failed: {}'.format(e))
		self.async_fetch()

	def async_fetch(self, ignore_cache: bool = False) -> bool:
		if not ignore_cache and time.time() - self.__meta_fetch_time <= self.CACHE_TTL:
			return False
		with self.__fetch_thread_lock:
			if self.__fetch_thread is not None:
				return False
			self.__fetch_thread = threading.Thread(target=self.__async_fetch, name='CatalogueMetaFetcher', daemon=True)
			self.__fetch_thread.start()
			return True

	def __async_fetch(self):
		try:
			t = time.time()
			meta_json = self._get_meta_json()
			meta = self._load_meta_json(meta_json)
		except Exception as e:
			self.logger.exception('Catalogue meta registry fetch failed: {}'.format(e))
		else:
			with self.__meta_lock:
				self.__meta_fetch_time = time.time()
				self.__meta = meta
				try:
					self.__save(meta_json, self.__meta_fetch_time)
				except Exception as e:
					self.logger.exception('Catalogue meta registry save failed: {}'.format(e))
				else:
					self.logger.info('Catalogue meta registry updated, cost {:.2f}s'.format(time.time() - t))
		finally:
			with self.__fetch_thread_lock:
				self.__fetch_thread = None
