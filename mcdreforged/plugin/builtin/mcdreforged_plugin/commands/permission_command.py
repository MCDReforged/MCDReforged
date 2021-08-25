import re
from typing import Optional

from mcdreforged.command.builder.exception import UnknownArgument
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RAction, RTextList, RColor
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.utils import string_util


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


class PermissionCommand(SubCommand):
	def get_command_node(self) -> Literal:
		def permission_player_node():
			return QuotableText('player').suggests(lambda: self.mcdr_server.permission_manager.get_players())

		return (
			self.control_command_root({'permission', 'perm'}).
			runs(lambda src: src.reply(self.get_help_message(src, 'mcdr_command.help_message.permission'))).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
			then(
				Literal('list').runs(lambda src: self.list_permission(src, None)).
				then(Text('level').runs(lambda src, ctx: self.list_permission(src, ctx['level'])))
			).
			then(Literal('set').then(permission_player_node().then(Text('level').runs(lambda src, ctx: self.set_player_permission(src, ctx['player'], ctx['level']))))).
			then(
				Literal({'query', 'q'}).runs(lambda src: self.query_self_permission(src)).
				then(permission_player_node().runs(lambda src, ctx: self.query_player_permission(src, ctx['player'])))
			).
			then(Literal({'remove', 'rm'}).then(permission_player_node().runs(lambda src, ctx: self.remove_player_permission(src, ctx['player'])))).
			then(Literal({'setdefault', 'setd'}).then(Text('level').runs(lambda src, ctx: self.set_default_permission(src, ctx['level']))))
		)

	def set_player_permission(self, source: CommandSource, player: str, value: str):
		permission_level = PermissionLevel.get_level(value)
		if permission_level is None:
			source.reply(self.tr('mcdr_command.invalid_permission_level'))
		elif not Validator.player_name(player):
			source.reply(self.tr('mcdr_command.invalid_player_name'))
		else:
			# Source with permission level x is allowed manipulate players/level in permission level range [0, x]
			if not source.has_permission(max(permission_level.level, self.mcdr_server.permission_manager.get_player_permission_level(player))):
				source.reply(self.tr('mcdr_command.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.set_permission_level(player, permission_level)
				if source.is_player:
					source.reply(self.tr('permission_manager.set_permission_level.done', player, permission_level.name))

	def query_self_permission(self, source: CommandSource):
		source.reply(self.tr('mcdr_command.query_player_permission.self', PermissionLevel.from_value(source.get_permission_level())))

	def query_player_permission(self, source: CommandSource, player: str):
		if not Validator.player_name(player):
			source.reply(self.tr('mcdr_command.invalid_player_name'))
			return
		else:
			level = self.mcdr_server.permission_manager.get_player_permission_level(player, auto_add=False)
			if level is not None:
				source.reply(self.tr('mcdr_command.query_player_permission.player', player, PermissionLevel.from_value(level)))
			else:
				source.reply(self.tr('mcdr_command.query_player_permission.player_unknown', player))

	def remove_player_permission(self, source: CommandSource, player: str):
		if not Validator.player_name(player):
			source.reply(self.tr('mcdr_command.invalid_player_name'))
		else:
			if not source.has_permission(self.mcdr_server.permission_manager.get_player_permission_level(player)):
				source.reply(self.tr('mcdr_command.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.remove_player(player)
				source.reply(self.tr('mcdr_command.remove_player_permission.player_removed', player))

	def list_permission(self, source: CommandSource, target_value: Optional[str]):
		specified_level = PermissionLevel.get_level(target_value)
		if specified_level is None:
			# show default level information if target permission not specified
			source.reply(
				RText(self.tr(
					'mcdr_command.list_permission.show_default',
					self.mcdr_server.permission_manager.get_default_permission_level()
				))
				.c(RAction.suggest_command, '{} permission setdefault '.format(self.control_command_prefix))
				.h(self.tr('mcdr_command.list_permission.suggest_setdefault'))
			)
		for permission_level in PermissionLevel.INSTANCES:
			if specified_level is None or permission_level == specified_level:
				source.reply(
					RText('§7[§e{}§7]§r'.format(permission_level.name))
					.c(RAction.run_command, '{} permission list {}'.format(self.control_command_prefix, permission_level.name))
					.h(self.tr('mcdr_command.list_permission.suggest_list', permission_level.name))
				)
				for player in self.mcdr_server.permission_manager.get_permission_group_list(permission_level.name):
					texts = RText('§7-§r {}'.format(player))
					if self.can_see_rtext(source):
						texts += RTextList(
							RText(' [✎]', color=RColor.gray)
							.c(RAction.suggest_command, '{} permission set {} '.format(self.control_command_prefix, string_util.auto_quotes(player)))
							.h(self.tr('mcdr_command.list_permission.suggest_set', player)),
							RText(' [×]', color=RColor.gray)
							.c(RAction.suggest_command, '{} permission remove {}'.format(self.control_command_prefix, string_util.auto_quotes(player)))
							.h(self.tr('mcdr_command.list_permission.suggest_disable', player)),
						)
					source.reply(texts)

	def set_default_permission(self, source: CommandSource, value: str):
		permission_level = PermissionLevel.get_level(value)
		if permission_level is None:
			source.reply(self.tr('mcdr_command.invalid_permission_level'))
		elif not source.has_permission(permission_level.level):
			source.reply(self.tr('mcdr_command.permission_not_enough'))
		else:
			self.mcdr_server.permission_manager.set_default_permission_level(permission_level)
			if source.is_player:
				source.reply(self.tr('permission_manager.set_default_permission_level.done', permission_level.name))

