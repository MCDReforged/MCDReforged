import dataclasses
from typing import Optional, List

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_base import PimCommandHandlerBase
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.texts import Texts
from mcdreforged.plugin.type.packed_plugin import PackedPlugin


@dataclasses.dataclass
class _FreezeItem:
	id: str
	version: str
	hash: Optional[str] = None

	def as_str(self) -> str:
		return self.as_text().to_plain_text()

	def as_text(self) -> RTextBase:
		args = [
			Texts.plugin_id(self.id),
			RText('==', RColor.gray),
			Texts.version(self.version),
		]
		if self.hash:
			args.extend([
				RText('@', RColor.gray),
				RText(self.hash, RColor.dark_green),
			])
		return RTextList(*args)


class PimFreezeCommandHandler(PimCommandHandlerBase):
	def process(self, source: CommandSource, context: CommandContext):
		freeze_all = context.get('all', 0) > 0
		with_hash = context.get('no_hash', 0) == 0
		output_path: Optional[str] = context.get('output')

		freeze_items: List[_FreezeItem] = []
		for plugin in self.plugin_manager.get_regular_plugins():
			if freeze_all or isinstance(plugin, PackedPlugin):
				item = _FreezeItem(id=plugin.get_id(), version=str(plugin.get_version()))
				if with_hash and isinstance(plugin, PackedPlugin):
					item.hash = 'sha256:' + plugin.get_file_sha256()
				freeze_items.append(item)

		if output_path is not None:
			try:
				with open(output_path, 'w', encoding='utf8') as f:
					for item in freeze_items:
						f.write(item.as_str())
						f.write('\n')
			except OSError as e:
				source.reply(self._tr('freeze.file_output.error', Texts.file_path(output_path), e).set_color(RColor.red))
			else:
				source.reply(self._tr('freeze.file_output.done', Texts.file_path(output_path)))
		else:
			source.reply(self._tr('freeze.direct_output.title_all' if freeze_all else 'freeze.direct_output.title', len(freeze_items)))
			for item in freeze_items:
				source.reply(item.as_text())
