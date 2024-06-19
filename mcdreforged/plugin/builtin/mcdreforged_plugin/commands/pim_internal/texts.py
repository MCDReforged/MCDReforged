from pathlib import Path
from typing import Any, Union, overload

from mcdreforged.minecraft.rtext.style import RColor, RAction, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.installer.dependency_resolver import PluginCandidate
from mcdreforged.plugin.meta.version import Version


class Texts:
	@classmethod
	@overload
	def candidate(cls, plugin_id: str, version: Union[str, Version]) -> RTextBase: ...

	@classmethod
	@overload
	def candidate(cls, candidate: PluginCandidate) -> RTextBase: ...

	@classmethod
	def candidate(cls, *args) -> RTextBase:
		if len(args) == 1:
			candidate: PluginCandidate = args[0]
			return cls.candidate(candidate.id, candidate.version)
		elif len(args) == 2:
			plugin_id: str = args[0]
			version: Union[str, Version] = args[1]
			return RTextList(
				cls.plugin_id(plugin_id),
				RText('@', RColor.gray),
				cls.version(version),
			)
		else:
			raise TypeError(len(args))

	@classmethod
	def cmd(cls, s: str, run: bool = False) -> RTextBase:
		return RText(s, color=RColor.gray).c(RAction.run_command if run else RAction.suggest_command, s)

	@classmethod
	def diff_version(cls, base: Version, new: Version) -> RTextBase:
		s1, s2 = str(base), str(new)
		i = 0
		for i in range(min(len(s1), len(s2))):
			if s1[i] != s2[i]:
				break
		if i == 0:
			return RText(s2, RColor.gold)
		else:
			return RText(s2[:i]) + RText(s2[i:], RColor.dark_aqua)

	@classmethod
	def file_name(cls, name: str) -> RTextBase:
		return RText(name, color=RColor.dark_aqua)

	@classmethod
	def file_path(cls, path: Union[str, Path]) -> RTextBase:
		return RText(path, color=RColor.dark_aqua).h(str(Path(path)))

	@classmethod
	def number(cls, n: Union[int, float]) -> RTextBase:
		return RText(n, color=RColor.yellow)

	@classmethod
	def plugin_id(cls, plugin_id: str) -> RTextBase:
		return RText(plugin_id, color=RColor.yellow)

	@classmethod
	def url(cls, s: Any, url: str, *, color: RColor = RColor.blue, underlined: bool = True) -> RTextBase:
		text = RText(s, color=color).c(RAction.open_url, url)
		if underlined:
			text.set_styles(RStyle.underlined)
		return text

	@classmethod
	def version(cls, version: Union[str, Version]) -> RTextBase:
		return RText(version, color=RColor.gold)
