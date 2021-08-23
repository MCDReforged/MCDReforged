from mcdreforged.command.builder.exception import UnknownArgument
from mcdreforged.command.builder.nodes.arguments import Text
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RColor, RAction
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand


class SetLanguageCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			self.control_command_root({'setlanguage', 'setlang'}).
			runs(lambda src: src.reply(self.get_help_message(src, 'mcdr_command.help_message.setlang'))).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
			then(
				Text('language').
				suggests(lambda: self.mcdr_server.translation_manager.available_languages).
				runs(lambda src, ctx: self.set_language(src, ctx['language']))
			)
		)

	def set_language(self, source: CommandSource, language: str):
		available_languages = self.mcdr_server.translation_manager.available_languages
		if language not in available_languages:
			source.reply(self.tr('mcdr_command.set_language.not_available', language))
			lang_texts = []
			for lang in available_languages:
				lang_texts.append(RText(lang, color=RColor.yellow).c(RAction.run_command, '{} setlang {}'.format(self.control_command_prefix, lang)))
			source.reply(self.tr('mcdr_command.set_language.language_list', RText.join(', ', lang_texts)))
		else:
			self.mcdr_server.config.set_value('language', language)
			self.mcdr_server.translation_manager.set_language(language)
			source.reply(self.tr('mcdr_command.set_language.success', language))
