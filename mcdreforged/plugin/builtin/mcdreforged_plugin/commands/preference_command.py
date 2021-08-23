from typing import Optional

from mcdreforged.command.builder.exception import RequirementNotMet
from mcdreforged.command.builder.nodes.arguments import QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RColor
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.preference.preference_manager import PreferenceItem


class PreferenceCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			self.public_command_root({'preference', 'pref'}).
			requires(lambda src: src.is_player).
			on_error(RequirementNotMet, lambda src: src.reply(self.tr('mcdr_command.preference.player_required').set_color(RColor.red)), handled=True).
			runs(lambda src: self.show_preferences(src, None)).
			then(
				QuotableText('option').
				suggests(lambda: list(PreferenceItem.get_annotations_fields().keys())).
				runs(lambda src, ctx: self.show_preferences(src, ctx['option'])).
				then(QuotableText('value').runs(lambda src, ctx: self.set_preference(src, ctx['option'], ctx['value'])))
			)
		)

	def show_preferences(self, source: CommandSource, specified_option: Optional[str] = None):
		pref = self.mcdr_server.preference_manager.get_preference(source, auto_add=True)
		source.reply(self.tr('mcdr_command.preference.list.title'))
		for option, value in pref.get_annotations_fields().items():
			if specified_option is None or option == specified_option:
				source.reply(RText.format('{} §7=§r {}', option, value))

	def set_preference(self, source: CommandSource, option: str, value: str):
		pref = self.mcdr_server.preference_manager.get_preference(source, auto_add=True)
		pref.set_field(option, value)
		self.mcdr_server.preference_manager.save_preferences()
		self.show_preferences(source, None)
		source.reply(self.tr('mcdr_command.preference.set.done', RText(option, ), value))

