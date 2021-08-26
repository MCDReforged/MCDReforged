from typing import NamedTuple, Any, List

from mcdreforged.command.builder.nodes.arguments import Integer
from mcdreforged.command.builder.nodes.basic import Literal, CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RAction, RColor
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.plugin.plugin_registry import HelpMessage

HELP_MESSAGE_PER_PAGE = 10


class FunctionCallResult(NamedTuple):
	return_value: Any
	no_error: bool


class HelpCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			Literal(self.help_command_prefix).
			runs(self.process_help_command).
			then(
				Integer('page').at_min(1).
				runs(self.process_help_command)
			)
		)

	def process_help_command(self, source: CommandSource, context: CommandContext):
		page = context.get('page')
		source.reply(self.tr('mcdr_command.help_message.title'))
		matched: List[HelpMessage] = []
		msg: HelpMessage
		for msg in self.mcdr_server.plugin_manager.registry_storage.help_messages:
			if source.has_permission(msg.permission):
				matched.append(msg)
		matched_count = len(matched)

		if page is not None:
			left, right = (page - 1) * HELP_MESSAGE_PER_PAGE, page * HELP_MESSAGE_PER_PAGE
		else:
			left, right = 0, matched_count
		for i in range(left, right):
			if 0 <= i < matched_count:
				msg = matched[i]
				source.reply(RText.format('{}: {}', RText(msg.prefix, color=RColor.gray).c(RAction.suggest_command, msg.prefix), msg.message))

		if page is not None:
			has_prev = 0 < left < matched_count
			has_next = 0 < right < matched_count
			color = {False: RColor.dark_gray, True: RColor.gray}
			prev_page = RText('<-', color=color[has_prev])
			if has_prev:
				prev_page.c(RAction.run_command, '{} {}'.format(self.help_command_prefix, page - 1)).h(self.tr('mcdr_command.help_message.previous_page_hover'))
			next_page = RText('->', color=color[has_next])
			if has_next:
				next_page.c(RAction.run_command, '{} {}'.format(self.help_command_prefix, page + 1)).h(self.tr('mcdr_command.help_message.next_page_hover'))

			source.reply(RText.format('{} {} {}', prev_page, self.tr('mcdr_command.help_message.page_number', page), next_page))
