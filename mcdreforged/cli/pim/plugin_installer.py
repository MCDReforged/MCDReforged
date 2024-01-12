import gzip
import io
import json
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Tuple, Iterable

from wcwidth import wcswidth

from mcdreforged.cli.pim.dependency_resolver import DependencyResolver, PluginRequirement
from mcdreforged.cli.pim.replier import Replier
from mcdreforged.minecraft.rtext.style import RStyle, RColor
from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils.types import MessageText


class Table:
	Row = Tuple[MessageText]

	def __init__(self, header: List[MessageText]):
		self.__rows: List[Tuple[MessageText]] = [tuple(header)]

	@property
	def __header(self) -> Row:
		return self.__rows[0]

	@property
	def width(self) -> int:
		return len(self.__header)

	@property
	def height(self) -> int:
		return len(self.__rows)

	def add_row(self, row: List[MessageText]):
		assert self.width == len(row), 'Table width mismatch, expected {}, new row width {}'.format(self.width, len(row))
		self.__rows.append(tuple(row))

	def dump(self) -> List[MessageText]:
		widths = []
		for j in range(len(self.__header)):
			widths.append(max(map(lambda r: wcswidth(str(r[j])), self.__rows)))
		lines = []
		for i, row in enumerate(self.__rows):
			items = []
			for j, cell in enumerate(row):
				if i == 0:
					cell = RTextBase.from_any(cell).set_styles(RStyle.bold)
				width = wcswidth(str(cell))
				if j != len(row) - 1 and width < widths[j]:
					cell += ' ' * (widths[j] - width)
				items.append(cell)
			lines.append(RTextBase.join('   ', items))
		return lines

	def dump_to(self, replier: Replier):
		for line in self.dump():
			replier.reply(line)


def get_with_retry(urls: Iterable[str]) -> bytes:
	errors = {}
	for url in urls:
		try:
			req = urllib.request.Request(url, method='GET')
			with urllib.request.urlopen(req, timeout=3) as response:
				return response.read()
		except (urllib.error.URLError, socket.error) as e:
			if isinstance(e, urllib.error.HTTPError):
				raise
			errors[url] = e
	else:
		raise urllib.error.URLError('All attempts failed: {}'.format(errors))


class MetaHolder:
	META_URLS = [
		'https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/{path}',
		'https://ghproxy.com/https://raw.githubusercontent.com/MCDReforged/PluginCatalogue/meta/{path}',
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
		content = get_with_retry(map(lambda u: u.format(path=path), self.urls))
		if path.endswith('.gz'):
			buf = io.BytesIO(content)
			with gzip.GzipFile(fileobj=buf) as gzf:
				content = gzf.read()
		return json.loads(content.decode('utf8'))


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
		return get_with_retry(urls)

	def test_stuffs(self):
		t = time.time()
		self.get_catalogue_meta()
		print('fetch everything.json.gz cost', time.time() - t)

	def list_plugin(self) -> int:
		meta = self.get_catalogue_meta()

		table = Table(['id', 'name', 'version', 'description'])
		na = RText('N/A', color=RColor.gray)
		for plugin_id, plugin in meta.get('plugins', {}).items():
			if plugin['release'].get('latest_version_index') is not None:
				release = plugin['release']['releases'][plugin['release']['latest_version_index']]
				version = release['meta']['version']
			else:
				version = na
			description = plugin['meta'].get('description', {})
			table.add_row([
				plugin_id, plugin['meta'].get('name', na),
				version, description.get(self.language, description.get(self.DEFAULT_LANGUAGE, na))
			])
		table.dump_to(self.replier)
		return 0

	def download_plugin(self, plugin_ids: List[str], target: str) -> int:
		target_dir = Path(target)
		if not target_dir.is_dir():
			self.print('{} is not a valid directory'.format(target))
			return 1

		meta = self.get_catalogue_meta()

		resolver = DependencyResolver(meta, {})
		result = resolver.resolve(list(map(PluginRequirement.of, plugin_ids)))
		return 0

		# TODO: resolve dependency
		downloaded_paths = []
		for plugin_id in plugin_ids:
			try:
				releases = meta['plugins'][plugin_id]['release'].get('releases', [])
			except urllib.error.HTTPError as e:
				if e.code == 404:
					print('Unknown plugin {}'.format(repr(plugin_id)))
					return 1
				raise
			for release in releases:
				release['formatted_version'] = Version(release['parsed_version'])
			releases.sort(key=lambda r: r['formatted_version'], reverse=True)

			for release in releases:
				# TODO: check dependency
				version = release['formatted_version']
				asset = release['assets'][0]
				break
			else:
				self.print('No release for plugin {}'.format(plugin_id))
				return 1

			file_path = target_dir / asset['name']
			self.print('Downloading {}@{} to {} ({:.1f}KB)'.format(plugin_id, version, file_path, asset['size'] / 1024.0))
			content = self.__download_release_file(asset['browser_download_url'])
			with open(file_path, 'wb') as f:
				f.write(content)
			downloaded_paths.append(file_path)

		self.print('Downloaded {} plugins: {}'.format(len(downloaded_paths), ', '.join(map(str, downloaded_paths))))
