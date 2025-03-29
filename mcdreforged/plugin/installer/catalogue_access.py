import functools
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Iterable

from wcwidth import wcswidth

from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData
from mcdreforged.utils.replier import Replier
from mcdreforged.utils.text_utils import Table
from mcdreforged.utils.types.message import MessageText


def is_subsequence(keyword: str, s: str):
	idx = 0
	for char in s:
		if idx < len(keyword) and char == keyword[idx]:
			idx += 1
	return idx == len(keyword)


class PluginCatalogueAccess:
	@classmethod
	def filter_sort(cls, plugins: Iterable[PluginData], keyword: Optional[str]) -> List[PluginData]:
		plugins: List[PluginData] = list(plugins)

		if keyword is None:
			return plugins

		def check_keyword(s: str, ss: bool = True):
			if ss:
				return s and is_subsequence(keyword.lower(), s.lower())
			else:
				return s and keyword.lower() in s.lower()

		scores: Dict[str, tuple] = {}
		for plugin in plugins:
			scores[plugin.id] = (
				check_keyword(plugin.id),
				check_keyword(plugin.name or ''),
				any(map(functools.partial(check_keyword, ss=False), plugin.description.values())),
			)

		def sort_key_getter(plg: PluginData):
			return scores[plg.id]

		plugins.sort(key=sort_key_getter, reverse=True)
		return [plg for plg in plugins if any(scores[plg.id])]

	@classmethod
	def list_plugin(
			cls, meta: MetaRegistry, replier: Replier, keyword: Optional[str], *,
			table_header: Optional[Tuple[MessageText, MessageText, MessageText, MessageText]] = None
	) -> int:
		def na_or_width_limited(s: Optional[str], n: int) -> MessageText:
			if s is None:
				return RText('N/A', color=RColor.gray)
			if n < 0:
				return s
			result = ''
			for ch in s:
				if wcswidth(new_s := result + ch) > n:
					return RText(result) + RText('...', color=RColor.gray)
				result = new_s
			return result

		plugins = cls.filter_sort(meta.plugins.values(), keyword)

		table = Table(table_header or ['ID', 'Name', 'Version', 'Description'])
		for plugin in plugins:
			table.add_row([
				plugin.id,
				na_or_width_limited(plugin.name, 48),
				na_or_width_limited(plugin.latest_version, 30),
				na_or_width_limited(plugin.description_for(replier.language), 256)
			])
		table.dump_to(replier)

		return len(plugins)

	@classmethod
	def download_plugin(cls, meta: MetaRegistry, replier: Replier, plugin_ids: List[str], target_dir: str) -> bool:
		target_dir = Path(target_dir)
		if not target_dir.is_dir():
			replier.reply('{} is not a valid directory'.format(target_dir))
			return False

		for plugin_id in plugin_ids:
			if plugin_id not in meta.plugins:
				replier.reply('Plugin {!r} does not exist'.format(plugin_id))
				return False

		downloaded_paths = []
		for plugin_id in plugin_ids:
			plugin = meta.plugins[plugin_id]
			if plugin.latest_version is None:
				replier.reply('Plugin {!r} does not have any release'.format(plugin_id))
				return False
			release = plugin.releases[plugin.latest_version]

			file_path = target_dir / release.file_name
			replier.reply('Downloading {}@{} to {} ({:.1f}KiB)'.format(plugin_id, release.version, file_path, release.file_size / 1024.0))
			ReleaseDownloader(release, file_path, replier).download(show_progress=ReleaseDownloader.ShowProgressPolicy.full)
			downloaded_paths.append(file_path)

		replier.reply('Downloaded {} plugin{}: {}'.format(len(plugin_ids), 's' if len(plugin_ids) > 0 else '', ', '.join(map(str, plugin_ids))))
		return True
