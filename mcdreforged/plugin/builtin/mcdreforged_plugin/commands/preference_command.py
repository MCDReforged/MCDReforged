from typing import TYPE_CHECKING, NamedTuple, Callable, Collection, Any, Type, Dict, List

from mcdreforged.command.builder.nodes.arguments import QuotableText
from mcdreforged.command.builder.nodes.basic import Literal, ArgumentNode
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RColor, RAction, RStyle, RTextList, RTextBase
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.preference.preference_manager import PreferenceItem

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin


PREF_COLOR = RColor.dark_aqua
VALUE_COLOR = RColor.gold


class PrefCommandEntry(NamedTuple):
	pref_name: str
	node_type: Type[ArgumentNode]
	suggester: Callable[[], Collection[str]]
	callback: Callable[[CommandSource, Any], Any]


class PreferenceCommand(SubCommand):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)

		def register(entry: PrefCommandEntry):
			self.preferences[entry.pref_name] = entry

		self.preferences: Dict[str, PrefCommandEntry] = {}
		register(PrefCommandEntry('language', QuotableText, lambda: self.available_languages, self.set_language))

	@property
	def available_languages(self) -> Collection[str]:
		return self.mcdr_server.translation_manager.available_languages

	def get_command_node(self) -> Literal:
		root_node = (
			self.public_command_root({'preference', 'pref'}).
			runs(lambda src: src.reply(self.get_help_message(src, 'mcdr_command.help_message.preference'))).
			then(Literal('list').runs(lambda src: self.show_preference_list(src)))
		)
		for pref in self.preferences.values():
			root_node.then(
				Literal(pref.pref_name).
				runs(lambda src, ctx: self.show_preference_item(src, pref.pref_name)).
				then(
					pref.node_type('value').
					suggests(pref.suggester).
					runs(lambda src, ctx: pref.callback(src, ctx['value']))
				)
			)
		return root_node

	def show_preference_list(self, source: CommandSource):
		pref = self.mcdr_server.preference_manager.get_preference(source, auto_add=True)
		source.reply(self.tr('mcdr_command.preference.list.title'))
		for pref_name in pref.get_annotations_fields().keys():
			value = getattr(pref, pref_name, RText('N/A', RColor.gray))
			source.reply(
				RTextList(RText('- ', RColor.gray), RText(pref_name, PREF_COLOR), RText(': ', RColor.gray), RText(value, VALUE_COLOR)).
				h(self.tr('mcdr_command.preference.list.detail_hint', RText(pref_name, PREF_COLOR))).
				c(RAction.run_command, '{} preference {}'.format(self.control_command_prefix, pref_name))
			)

	def show_preference_item(self, source: CommandSource, pref_name: str):
		pref_mgr = self.mcdr_server.preference_manager
		entry: PrefCommandEntry = self.preferences.get(pref_name)
		pref: PreferenceItem = pref_mgr.get_preference(source, auto_add=True)
		current_value = getattr(pref, pref_name, None)
		default_value = getattr(pref_mgr.get_default_preference(), pref_name, None)
		if entry is None or current_value is None:  # should never come here
			raise KeyError('Unknown preference {}'.format(pref_name))

		def get_suggestion_text(value: str):
			text = RText(value, VALUE_COLOR).c(RAction.suggest_command, '{} preference {} {}'.format(self.control_command_prefix, pref_name, value))
			hover_text = RTextList(self.tr('mcdr_command.preference.item.set_suggestion_hint', RText(pref_name, PREF_COLOR), RText(value, VALUE_COLOR)))
			styles: List[RStyle] = []
			extra_descriptions: List[RTextBase] = []
			if value == current_value:
				styles.append(RStyle.underlined)
				extra_descriptions.append(self.tr('mcdr_command.preference.item.current'))
			if value == default_value:
				styles.append(RStyle.bold)
				extra_descriptions.append(self.tr('mcdr_command.preference.item.default'))
			if len(extra_descriptions) > 0:
				hover_text.append(RTextList('\n', RText.join(', ', extra_descriptions)))
			text.set_styles(styles)
			return text.h(hover_text)

		source.reply(self.tr('mcdr_command.preference.item.name', RText(pref_name, PREF_COLOR)))
		source.reply(self.tr('mcdr_command.preference.item.value', RText(current_value, VALUE_COLOR)))
		source.reply(self.tr('mcdr_command.preference.item.suggestions', RText.join(', ', map(get_suggestion_text, entry.suggester()))))

	def set_language(self, source: CommandSource, new_lang: str):
		if new_lang not in self.available_languages:
			source.reply(self.tr('mcdr_command.preference.unknown_language', new_lang))
			return
		pref = self.mcdr_server.preference_manager.get_preference(source, auto_add=True)
		pref.language = new_lang
		self.mcdr_server.preference_manager.save_preferences()
		source.reply(self.tr('mcdr_command.preference.set.done', RText('language', RColor.yellow), RText(new_lang, RColor.gold)))
