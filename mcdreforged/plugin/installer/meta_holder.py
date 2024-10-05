import datetime
import gzip
import json
import lzma
import re
import threading
import time
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Callable, Any, TYPE_CHECKING

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData, EmptyMetaRegistry
from mcdreforged.utils import request_utils, time_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.logging.logger import MCDReforgedLogger


class CatalogueMetaRegistry(MetaRegistry):
	def __init__(self, plugin: Dict[str, PluginData]):
		self.__plugins = plugin

	@property
	@override
	def plugins(self) -> Dict[str, PluginData]:
		return self.__plugins


class CatalogueMetaRegistryHolder:
	def __init__(self, *, meta_json_url: Optional[str] = None, meta_fetch_timeout: Optional[float] = None):
		self.__meta_json_url: str = ''
		self.__meta_fetch_timeout: float = 0
		self.set_meta_json_url(meta_json_url)
		self.set_meta_fetch_timeout(meta_fetch_timeout)

	def set_meta_json_url(self, meta_json_url: Optional[str] = None):
		if meta_json_url is None:
			meta_json_url = core_constant.PLUGIN_CATALOGUE_META_URL
		self.__meta_json_url = meta_json_url

	def set_meta_fetch_timeout(self, meta_fetch_timeout: Optional[float] = None):
		if meta_fetch_timeout is None:
			meta_fetch_timeout = 10
		self.__meta_fetch_timeout = meta_fetch_timeout

	def get_registry(self) -> MetaRegistry:
		meta_json = self._fetch_meta_json()
		return self._load_meta_json(meta_json)

	def _fetch_meta_json(self) -> dict:
		max_size = 20 * 2 ** 20  # 20MiB limit. In 2024-03-14, the uncompressed size is only 545KiB
		buf = request_utils.get_buf(self.__meta_json_url, 'MetaFetcher', timeout=self.__meta_fetch_timeout, max_size=max_size)

		if self.__meta_json_url.endswith('.gz'):
			with gzip.GzipFile(fileobj=BytesIO(buf)) as gzip_f:
				content = gzip_f.read(max_size + 1)
		elif self.__meta_json_url.endswith('.xz'):
			content = lzma.LZMADecompressor().decompress(buf, max_size + 1)
		else:
			content = buf

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

			plugin_info: dict = aop['plugin']
			repos_url = plugin_info.get('repository', '')
			if (repos_match := re.fullmatch(r'https://github\.com/([^/]+)/([^/]+)/?', repos_url)) is None:
				continue

			plugin_data = PluginData(
				id=plugin_id,
				name=meta.get('name'),
				repos_url=repos_url,
				repos_owner=repos_match.group(1),
				repos_name=repos_match.group(2),
				latest_version=latest_version,
				description=meta.get('description', {}),
			)
			for release in release_summary['releases']:
				meta: dict = release['meta']
				asset: dict = release['asset']
				release_data = ReleaseData(
					version=meta['version'],
					tag_name=release['tag_name'],
					url=release['url'],
					created_at=datetime.datetime.fromisoformat(release['created_at'].rstrip('Z')),
					dependencies=meta.get('dependencies', {}),
					requirements=meta.get('requirements', []),
					asset_id=asset['id'],
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


class BackgroundMetaFetcher(BackgroundThreadExecutor):
	def __init__(self, logger: 'MCDReforgedLogger', tick_func: Callable[[], Any]):
		super().__init__(logger)
		self.__tick_func = tick_func

	@override
	def get_name(self) -> str:
		return 'CatalogueMetaFetcher'

	@override
	def tick(self):
		self.__tick_func()
		time.sleep(0.1)


class PersistCatalogueMetaRegistryHolder(CatalogueMetaRegistryHolder):
	_FetchStartCallbackOpt = Optional[Callable[[bool], None]]
	_FetchCallbackOpt = Optional[Callable[[Optional[Exception]], None]]
	_FetchBlockedOpt = Optional[Callable[[], None]]

	def __init__(self, mcdr_server: 'MCDReforgedServer', cache_path: Path, *, meta_json_url: str, meta_fetch_timeout: float, meta_cache_ttl: float):
		super().__init__(meta_json_url=meta_json_url, meta_fetch_timeout=meta_fetch_timeout)
		self.logger: 'MCDReforgedLogger' = mcdr_server.logger
		self.__tr = mcdr_server.create_internal_translator('plugin_catalogue_meta_registry').tr
		self.__cache_path = cache_path
		self.__meta_lock = threading.Lock()
		self.__meta: MetaRegistry = EmptyMetaRegistry()
		self.__meta_cache_ttl = meta_cache_ttl
		self.__last_meta_fetch_time: float = 0
		self.__background_fetch_flag = False
		self.__fetch_lock = threading.Lock()
		self.__background_fetcher = BackgroundMetaFetcher(self.logger, self.__background_fetch)

	def set_meta_cache_ttl(self, meta_cache_ttl: float):
		self.__meta_cache_ttl = meta_cache_ttl

	@override
	def get_registry(self) -> MetaRegistry:
		self.__background_fetch_flag = True
		return self.__meta

	def get_registry_blocked(
			self,
			ignore_ttl: bool = False,
			start_callback: _FetchStartCallbackOpt = None,
			done_callback: _FetchCallbackOpt = None,
			blocked_callback: _FetchBlockedOpt = None,
	) -> MetaRegistry:
		if not self.__fetch_lock.acquire(blocking=False):
			if blocked_callback is not None:
				blocked_callback()
			self.__fetch_lock.acquire(blocking=True)
		try:
			self.__do_fetch(ignore_ttl=ignore_ttl, start_callback=start_callback, done_callback=done_callback)
		finally:
			self.__fetch_lock.release()
		return self.__meta

	def __load_cached_file(self):
		if not self.__cache_path.is_file():
			return
		try:
			with lzma.open(self.__cache_path, 'rt', encoding='utf8') as f:
				data: dict = json.load(f)
			meta = self._load_meta_json(data['meta'])
		except (KeyError, ValueError, OSError) as e:
			self.logger.exception(self.__tr('load_cached_failed', self.__cache_path, e))
			return

		with self.__meta_lock:
			self.__meta = meta
			self.__last_meta_fetch_time = float(data.get('timestamp', 0))

		self.logger.info(self.__tr(
			'load_cached_success',
			time_utils.format_time('%Y-%m-%d %H:%M:%S', self.__last_meta_fetch_time) or 'N/A',
		))

	def __save(self, meta_json: dict, timestamp: float):
		data = {
			'timestamp': timestamp,
			'meta': meta_json,
		}
		self.__cache_path.parent.mkdir(parents=True, exist_ok=True)
		with lzma.open(self.__cache_path, 'wt', encoding='utf8') as f:
			json.dump(data, f)

	def init(self):
		self.__load_cached_file()

		self.__background_fetcher.start()

	def terminate(self):
		self.__background_fetcher.stop()

	def __background_fetch(self):
		with self.__fetch_lock:
			# if the ttl is set to a very small number, don't keep fetching without stopping
			adjusted_ttl = max(10.0, self.__meta_cache_ttl)

			# flag set, and existing meta cache is expired
			if self.__background_fetch_flag and time.time() - self.__last_meta_fetch_time > adjusted_ttl:
				self.__background_fetch_flag = False
				self.__do_fetch(ignore_ttl=False, show_error_stacktrace=False)

	def __do_fetch(
			self,
			ignore_ttl: bool,
			start_callback: _FetchStartCallbackOpt = None,
			done_callback: _FetchCallbackOpt = None,
			*,
			show_error_stacktrace: bool = True
	):
		"""
		self.__fetch_lock should be acquired before calling this
		:return: true: processed (succeed or fail), false: skipped
		"""
		if done_callback is None:
			def done_callback(_):
				pass
		if start_callback is None:
			def start_callback(_):
				pass

		try:
			now = time.time()
			if not ignore_ttl and now - self.__last_meta_fetch_time <= self.__meta_cache_ttl:
				start_callback(False)
				done_callback(None)
				return
			start_time = now
			start_callback(True)

			meta_json = self._fetch_meta_json()
			meta = self._load_meta_json(meta_json)
		except Exception as e:
			if show_error_stacktrace:
				self.logger.exception('Catalogue meta registry fetch failed: {}'.format(e))
			else:
				self.logger.error('Catalogue meta registry fetch failed: ({}) {}'.format(type(e), e))
			done_callback(e)
		else:
			self.__last_meta_fetch_time = now
			with self.__meta_lock:
				self.__meta = meta
				try:
					self.__save(meta_json, self.__last_meta_fetch_time)
				except Exception as e:
					self.logger.exception('Catalogue meta registry save failed: {}'.format(e))
					done_callback(e)
				else:
					self.logger.debug('Catalogue meta registry updated, cost {:.2f}s'.format(time.time() - start_time))
				done_callback(None)
