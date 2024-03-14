import dataclasses
import functools
import operator
import re
import time
from pathlib import Path
from typing import List, Optional

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText
from mcdreforged.plugin.installer.dependency_resolver import DependencyResolver, PluginRequirement, PluginResolution, PackageResolution
from mcdreforged.plugin.installer.meta_holder import MetaHolder, MetaCache
from mcdreforged.plugin.installer.printer import Table
from mcdreforged.plugin.installer.replier import Replier
from mcdreforged.utils import request_util
from mcdreforged.utils.types import MessageText


def is_subsequence(keyword: str, s: str):
	idx = 0
	for char in s:
		if idx < len(keyword) and char == keyword[idx]:
			idx += 1
	return idx == len(keyword)


@dataclasses.dataclass
class ResolutionResult:
	plugins: PluginResolution = dataclasses.field(default_factory=dict)
	packages: PackageResolution = dataclasses.field(default_factory=list)


class PluginInstaller:
	DOWNLOAD_MIRROR_PREFIXES = [
		'https://mirror.ghproxy.com/',
		'https://hub.gitmirror.com/',
	]
	DEFAULT_LANGUAGE = 'en_us'

	def __init__(self, replier: Replier, language: str = DEFAULT_LANGUAGE, meta_holder: Optional[MetaHolder] = None):
		self.language = language
		self.replier = replier
		if meta_holder is None:
			meta_holder = MetaHolder()
		self.meta_holder = meta_holder

	def print(self, message: MessageText):
		self.replier.reply(message)

	def get_catalogue_meta(self) -> MetaCache:
		self.print('Fetching catalogue meta')
		return self.meta_holder.get()

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
		print('fetch everything.json.xz cost', time.time() - t)

	def run(self):
		pass

	def list_plugin(self, keyword: Optional[str]) -> int:
		def check_keyword(s: str, ss: bool = True):
			if ss:
				return s and is_subsequence(keyword.lower(), s.lower())
			else:
				return s and keyword.lower() in s.lower()

		meta = self.get_catalogue_meta()

		na = RText('N/A', color=RColor.gray)
		rows = []
		for plugin_id, plugin in meta.plugins.items():
			version = plugin.latest_version or na

			if keyword is not None:
				score = (
					check_keyword(plugin_id),
					check_keyword(plugin.name or ''),
					any(map(functools.partial(check_keyword, ss=False), plugin.description.values())),
				)
				if not any(score):
					continue
			else:
				score = 0

			rows.append((score, [
				plugin_id, plugin.name or na,
				version, plugin.description.get(self.language, plugin.description.get(self.DEFAULT_LANGUAGE, na))
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

		resolver = DependencyResolver(meta)
		result = resolver.resolve(list(map(PluginRequirement.of, plugin_ids)))

		downloaded_paths = []
		for plugin_id, version in result.items():
			release = meta.plugins[plugin_id].releases[str(version)]

			file_path = target_dir / release.file_name
			self.print('Downloading {}@{} to {} ({:.1f}KB)'.format(plugin_id, version, file_path, release.file_size / 1024.0))
			content = self.__download_release_file(release.file_url)
			with open(file_path, 'wb') as f:
				f.write(content)
			downloaded_paths.append(file_path)

		self.print('Downloaded {} plugins: {}'.format(len(downloaded_paths), ', '.join(map(str, downloaded_paths))))

	def __create_package_resolution(self, plugin_resolution: PluginResolution) -> PackageResolution:
		res: PackageResolution = []
		for plugin_id, version in plugin_resolution.items():
			r = self.meta_holder.get_release(plugin_id, str(version))
			res.extend(r.requirements)
		# TODO: deduplicate, ensure no conflict
		return res

	def resolve(self, plugin_requirements: List[PluginRequirement]) -> ResolutionResult:
		resolver = DependencyResolver(self.get_catalogue_meta())

		result = ResolutionResult()
		result.plugins = resolver.resolve(plugin_requirements)
		result.packages = self.__create_package_resolution(result.plugins)
		return result
