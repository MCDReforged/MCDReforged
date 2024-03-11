import functools
import gzip
import io
import json
import operator
import re
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText
from mcdreforged.plugin.installer.dependency_resolver import DependencyResolver, PluginRequirement
from mcdreforged.plugin.installer.printer import Table
from mcdreforged.plugin.installer.replier import Replier
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils import request_util
from mcdreforged.utils.types import MessageText


class MetaHolder:
	META_URLS = [
		'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/{path}',
		'https://mirror.ghproxy.com/https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/{path}',
		'https://raw.gitmirror.com/MCDReforged/PluginCatalogue/meta/{path}',
		'https://cdn.jsdelivr.net/gh/MCDReforged/PluginCatalogue@meta/{path}',
	]

	def __init__(self):
		self.urls = self.META_URLS.copy()
		self.__meta_cache = None
		self.__meta_cache_lock = threading.Lock()

	def fetch(self) -> dict:
		# TODO cache TTL
		if self.__meta_cache is not None:
			return self.__meta_cache
		with self.__meta_cache_lock:
			self.__meta_cache = self.__get_meta_json('everything.json.gz')
			return self.__meta_cache

	def __get_meta_json(self, path: str) -> dict:
		content = request_util.get_with_retry(map(lambda u: u.format(path=path), self.urls))
		if path.endswith('.gz'):
			buf = io.BytesIO(content)
			with gzip.GzipFile(fileobj=buf) as gzf:
				content = gzf.read()
		return json.loads(content.decode('utf8'))


def is_subsequence(keyword: str, s: str):
	idx = 0
	for char in s:
		if idx < len(keyword) and char == keyword[idx]:
			idx += 1
	return idx == len(keyword)


class PluginInstaller:
	DOWNLOAD_MIRROR_PREFIXES = [
		'https://mirror.ghproxy.com/',
		'https://hub.gitmirror.com/',
	]
	DEFAULT_LANGUAGE = 'en_us'

	def __init__(self, replier: Replier, language: str = DEFAULT_LANGUAGE):
		self.language = language
		self.replier = replier
		self.meta_holder = MetaHolder()

	def print(self, message: MessageText):
		self.replier.reply(message)

	def get_catalogue_meta(self) -> dict:
		self.print('Fetching catalogue meta')
		return self.meta_holder.fetch()

	def __download_release_file(self, url: str) -> bytes:
		urls = [url]
		if re.fullmatch(r'https://github\.com/[^/]+/[^/]+/releases/.+', url):
			for prefix in self.DOWNLOAD_MIRROR_PREFIXES:
				urls.append(prefix + url)
		# TODO: log if unknown
		return request_util.get_with_retry(urls)

	def test_stuffs(self):
		t = time.time()
		self.get_catalogue_meta()
		print('fetch everything.json.gz cost', time.time() - t)

	def list_plugin(self, keyword: Optional[str]) -> int:
		def check_keyword(s: str, ss: bool = True):
			if ss:
				return s and is_subsequence(keyword.lower(), s.lower())
			else:
				return s and keyword.lower() in s.lower()

		meta = self.get_catalogue_meta()

		na = RText('N/A', color=RColor.gray)
		rows = []
		for plugin_id, plugin in meta.get('plugins', {}).items():
			if plugin['release'].get('latest_version_index') is not None:
				release = plugin['release']['releases'][plugin['release']['latest_version_index']]
				meta = release['meta']
				version = meta['version']
			else:
				meta = plugin['meta']
				version = na
			description = meta.get('description', {})

			if keyword is not None:
				score = (
					check_keyword(plugin_id),
					check_keyword(plugin['meta'].get('name', '')),
					any(map(functools.partial(check_keyword, ss=False), description.values())),
				)
				if not any(score):
					continue
			else:
				score = 0

			rows.append((score, [
				plugin_id, plugin['meta'].get('name', na),
				version, description.get(self.language, description.get(self.DEFAULT_LANGUAGE, na))
			]))

		rows.sort(key=operator.itemgetter(0), reverse=True)
		table = Table(['id', 'name', 'version', 'description'])
		for _, row in rows:
			table.add_row(row)
		table.dump_to(self.replier)
		return 0

	def download_plugin(self, plugin_ids: List[str], target_dir: str) -> int:
		target_dir = Path(target_dir)
		if not target_dir.is_dir():
			self.print('{} is not a valid directory'.format(target_dir))
			return 1

		meta = self.get_catalogue_meta()

		resolver = DependencyResolver(meta, {})
		result = resolver.resolve(list(map(PluginRequirement.of, plugin_ids)))

		downloaded_paths = []
		for plugin_id, version in result.items():
			for release in meta['plugins'][plugin_id]['release'].get('releases', []):
				if Version(release['meta']['version']) == version:
					break
			else:
				self.print('No release for plugin {} v{}'.format(plugin_id, version))
				return 1

			asset = release['asset']
			file_path = target_dir / asset['name']
			self.print('Downloading {}@{} to {} ({:.1f}KB)'.format(plugin_id, version, file_path, asset['size'] / 1024.0))
			content = self.__download_release_file(asset['browser_download_url'])
			with open(file_path, 'wb') as f:
				f.write(content)
			downloaded_paths.append(file_path)

		self.print('Downloaded {} plugins: {}'.format(len(downloaded_paths), ', '.join(map(str, downloaded_paths))))
