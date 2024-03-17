import functools
import operator
import time
from pathlib import Path
from typing import Optional, List

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.meta_holder import CatalogueMetaRegistryHolder
from mcdreforged.plugin.installer.printer import Table
from mcdreforged.plugin.installer.replier import Replier
from mcdreforged.plugin.installer.types import MetaRegistry
from mcdreforged.utils.types import MessageText


def is_subsequence(keyword: str, s: str):
	idx = 0
	for char in s:
		if idx < len(keyword) and char == keyword[idx]:
			idx += 1
	return idx == len(keyword)


class PluginCatalogueAccess:
	def __init__(self, replier: Replier, meta_holder: Optional[CatalogueMetaRegistryHolder] = None):
		self.replier = replier
		if meta_holder is None:
			meta_holder = CatalogueMetaRegistryHolder()
		self.meta_holder = meta_holder

	def print(self, message: MessageText):
		self.replier.reply(message)

	def get_catalogue_meta(self) -> MetaRegistry:
		self.print('Fetching catalogue meta')
		return self.meta_holder.get_registry()

	# ======================= Operations =======================

	def test_stuffs(self):
		t = time.time()
		self.get_catalogue_meta()
		print('fetch everything.json.xz cost', time.time() - t)

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
				version, plugin.description.get(self.replier.language, plugin.description.get(self.replier.DEFAULT_LANGUAGE, na))
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

		# TODO: resolve dependencies if required

		meta = self.get_catalogue_meta()
		for plugin_id in plugin_ids:
			if plugin_id not in meta.plugins:
				self.print('Plugin {!r} does not exist'.format(plugin_id))
				return 1

		downloaded_paths = []
		for plugin_id in plugin_ids:
			plugin = meta.plugins[plugin_id]
			if plugin.latest_version is None:
				self.print('Plugin {!r} does not have any release'.format(plugin_id))
				return 1
			release = plugin.releases[plugin.latest_version]

			file_path = target_dir / release.file_name
			self.print('Downloading {}@{} to {} ({:.1f}KiB)'.format(plugin_id, release.version, file_path, release.file_size / 1024.0))
			ReleaseDownloader(release, file_path, self.replier).download(show_progress=True)
			downloaded_paths.append(file_path)

		self.print('Downloaded {} plugin{}: {}'.format(len(plugin_ids), 's' if len(plugin_ids) > 0 else '', ', '.join(map(str, plugin_ids))))
