import collections
import os
import re
import threading
import traceback
from typing import Callable, Any, Tuple, List, Optional

from mcdreforged import constant
from mcdreforged.command.builder.command_node import Literal, QuotableText, Text, GreedyText, Integer
from mcdreforged.command.builder.exception import UnknownArgument, RequirementNotMet, CommandError
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext import RText, RAction, RTextList, RStyle, RColor
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.permanent.permanent_plugin import PermanentPlugin
from mcdreforged.plugin.plugin import AbstractPlugin, PluginState
from mcdreforged.plugin.plugin_event import MCDRPluginEvents, EventListener
from mcdreforged.plugin.plugin_registry import HelpMessage
from mcdreforged.plugin.regular_plugin import RegularPlugin
from mcdreforged.utils import file_util, string_util

METADATA = {
	'id': constant.NAME.lower(),
	'version': constant.VERSION,
	'name': constant.NAME,
	'description': 'The core of {}'.format(constant.NAME),
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/Fallen-Breath/MCDReforged'
}
HELP_MESSAGE_PER_PAGE = 10


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


class MCDReforgedPlugin(PermanentPlugin):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager)
		self.metadata = Metadata(self, METADATA)
		self.tr = plugin_manager.mcdr_server.tr

	def get_metadata(self) -> Metadata:
		return self.metadata

	def get_fallback_metadata_id(self) -> str:
		raise RuntimeError()

	def load(self):
		self.plugin_registry.clear()
		self.set_state(PluginState.READY)
		self.__register_event_listeners()
		self.__register_help_messages()
		self.__register_commands()

	def __register_event_listeners(self):
		self.register_event_listener(MCDRPluginEvents.GENERAL_INFO, EventListener(self, self.on_info, 10))

	def on_info(self, server_interface, info):
		# maybe maybe
		pass

	def __repr__(self):
		# avoid using self.metadata here since it might not be initialized
		return 'MCDReforgedPlugin[version={}]'.format(METADATA['version'])

	@classmethod
	def get_control_command_prefix(cls):
		return '!!MCDR'

	@classmethod
	def get_help_command_prefix(cls):
		return '!!help'

	def __register_commands(self):
		self.register_command(
			Literal(self.get_control_command_prefix()).
			requires(lambda src: src.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL)).
			runs(lambda src: src.reply(self.get_help_message('mcdr_command.help_message'))).
			on_error(RequirementNotMet, self.on_mcdr_command_permission_denied, handled=True).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument, handled=True).
			then(
				Literal({'r', 'reload'}).
				runs(lambda src: src.reply(self.get_help_message('mcdr_command.help_message_reload'))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
				then(Literal({'plugin', 'plg'}).runs(self.refresh_changed_plugins)).
				then(Literal({'config', 'cfg'}).runs(self.reload_config)).
				then(Literal({'permission', 'perm'}).runs(self.reload_permission)).
				then(Literal('all').runs(self.reload_all))
			).
			then(
				Literal('status').runs(self.print_mcdr_status)
			).
			then(
				Literal({'permission', 'perm'}).
				runs(lambda src: src.reply(self.get_help_message('mcdr_command.help_message_permission'))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
				then(
					Literal('list').runs(lambda src: self.list_permission(src, None)).
					then(Text('level').runs(lambda src, ctx: self.list_permission(src, ctx['level'])))
				).
				then(Literal('set').then(QuotableText('player').then(Text('level').runs(lambda src, ctx: self.set_player_permission(src, ctx['player'], ctx['level']))))).
				then(
					Literal({'query', 'q'}).runs(lambda src: self.query_self_permission(src)).
					then(QuotableText('player').runs(lambda src, ctx: self.query_player_permission(src, ctx['player'])))
				).
				then(Literal({'remove', 'rm'}).then(QuotableText('player').runs(lambda src, ctx: self.remove_player_permission(src, ctx['player'])))).
				then(Literal({'setdefault', 'setd'}).then(Text('level').runs(lambda src, ctx: self.set_default_permission(src, ctx['level']))))
			).
			then(
				Literal({'plugin', 'plg'}).
				runs(lambda src: src.reply(self.get_help_message('mcdr_command.help_message_plugin'))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
				then(Literal('list').runs(self.list_plugin)).
				then(Literal('info').then(GreedyText('plugin_id').runs(lambda src, ctx: self.show_plugin_info(src, ctx['plugin_id'])))).
				then(Literal('load').then(GreedyText('file_name').runs(lambda src, ctx: self.load_plugin(src, ctx['file_name'])))).
				then(Literal('enable').then(GreedyText('file_name').runs(lambda src, ctx: self.enable_plugin(src, ctx['file_name'])))).
				then(Literal('reload').then(GreedyText('plugin_id').runs(lambda src, ctx: self.reload_plugin(src, ctx['plugin_id'])))).
				then(Literal('unload').then(GreedyText('plugin_id').runs(lambda src, ctx: self.unload_plugin(src, ctx['plugin_id'])))).
				then(Literal('disable').then(GreedyText('plugin_id').runs(lambda src, ctx: self.disable_plugin(src, ctx['plugin_id'])))).
				then(Literal({'reloadall', 'ra'}).runs(self.reload_all_plugin))
			).
			then(
				Literal({'checkupdate', 'cu'}).runs(lambda src: self.mcdr_server.update_helper.check_update(condition_check=lambda: True, reply_func=src.reply))
			)
		)
		self.register_command(
			Literal(self.get_help_command_prefix()).
			runs(self.process_help_command).
			then(
				Integer('page').at_min(1).
				runs(self.process_help_command)
			)
		)

	# ==============================
	#     Command Implementation
	# ==============================

	@staticmethod
	def can_see_rtext(source: CommandSource):
		return source.is_player

	def get_help_message(self, translation_key):
		lst = RTextList()
		for line in self.tr(translation_key).splitlines(keepends=True):
			prefix = re.search(r'(?<=§7)!!MCDR[\w ]*(?=§)', line)
			if prefix is not None:
				lst.append(RText(line).c(RAction.suggest_command, prefix.group()))
			else:
				lst.append(line)
		return lst

	def on_mcdr_command_permission_denied(self, source: CommandSource, error: CommandError):
		source.reply(RText(self.mcdr_server.tr('mcdr_command.permission_denied'), color=RColor.red))

	def on_mcdr_command_unknown_argument(self, source: CommandSource, error: CommandError):
		command = error.get_parsed_command()
		source.reply(
			RText(self.tr('mcdr_command.command_not_found', command)).
			h(self.tr('mcdr_command.command_not_found_suggest', command)).
			c(RAction.run_command, command)
		)

	FunctionCallResult = collections.namedtuple('FunctionCallResult', 'return_value no_error')

	def function_call(self, source: CommandSource, func: Callable[[], Any], name: str, log_success=True, log_fail=True, msg_args=()) -> FunctionCallResult:
		try:
			ret = self.FunctionCallResult(func(), True)
			if log_success:
				source.reply(self.tr('mcdr_command.{}.success'.format(name), *msg_args))
			return ret
		except:
			if log_fail:
				source.reply(self.tr('mcdr_command.{}.fail'.format(name), *msg_args))
			self.mcdr_server.logger.error(traceback.format_exc())
			return self.FunctionCallResult(None, False)

	# ----------
	#   Reload
	# ----------

	def __print_plugin_operation_result_if_no_error(self, source: CommandSource, ret: FunctionCallResult):
		if ret.no_error:
			source.reply(self.mcdr_server.plugin_manager.last_operation_result.to_rtext(show_path=source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL)))

	def refresh_changed_plugins(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', log_success=False)
		self.__print_plugin_operation_result_if_no_error(source, ret)

	def reload_config(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.load_config, 'reload_config')

	def reload_permission(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.permission_manager.load_permission_file, 'reload_permission')

	def reload_all(self, source: CommandSource):
		self.reload_config(source)
		self.reload_permission(source)
		self.refresh_changed_plugins(source)

	# --------------
	#   Permission
	# --------------

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
				.c(RAction.suggest_command, '!!MCDR permission setdefault ')
				.h(self.tr('mcdr_command.list_permission.suggest_setdefault'))
			)
		for permission_level in PermissionLevel.INSTANCES:
			if specified_level is None or permission_level == specified_level:
				source.reply(
					RText('§7[§e{}§7]§r'.format(permission_level.name))
					.c(RAction.run_command, '!!MCDR permission list {}'.format(permission_level.name))
					.h(self.tr('mcdr_command.list_permission.suggest_list', permission_level.name))
				)
				for player in self.mcdr_server.permission_manager.get_permission_group_list(permission_level.name):
					texts = RText('§7-§r {}'.format(player))
					if self.can_see_rtext(source):
						texts += RTextList(
							RText(' [✎]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission set {} '.format(string_util.auto_quotes(player)))
							.h(self.tr('mcdr_command.list_permission.suggest_set', player)),
							RText(' [×]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission remove {}'.format(string_util.auto_quotes(player)))
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

	# ----------
	#   Status
	# ----------

	def print_mcdr_status(self, source: CommandSource):
		def bool_formatter(bl):
			return '{}{}§r'.format('§a' if bl else '§7', bl)
		rcon_status_dict = {
			True: self.tr('mcdr_command.print_mcdr_status.online'),
			False: self.tr('mcdr_command.print_mcdr_status.offline')
		}

		source.reply(RTextList(
			RText(self.tr('mcdr_command.print_mcdr_status.line1', constant.NAME, constant.VERSION)).c(RAction.open_url, constant.GITHUB_URL).h(RText(constant.GITHUB_URL, styles=RStyle.underlined, color=RColor.blue)), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line2', self.tr(self.mcdr_server.mcdr_state.value))), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line3', self.tr(self.mcdr_server.server_state.value))), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line4', bool_formatter(self.mcdr_server.is_server_startup()))), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line5', bool_formatter(self.mcdr_server.is_exit_naturally()))), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line6', rcon_status_dict[self.mcdr_server.server_interface.is_rcon_running(is_plugin_call=False)])), '\n',
			RText(self.tr('mcdr_command.print_mcdr_status.line7', len(self.mcdr_server.plugin_manager.plugins))).c(RAction.suggest_command, '!!MCDR plugin list')
		))
		if source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
			source.reply(RTextList(
				self.tr('mcdr_command.print_mcdr_status.extra_line1', self.mcdr_server.process.pid if self.mcdr_server.process is not None else '§rN/A§r'), '\n',
				self.tr('mcdr_command.print_mcdr_status.extra_line2', self.mcdr_server.task_executor.task_queue.qsize(), constant.MAX_TASK_QUEUE_SIZE), '\n',
				self.tr('mcdr_command.print_mcdr_status.extra_line3', threading.active_count())
			))
			for thread in threading.enumerate():
				source.reply('  §r-§r {}'.format(thread.getName()))

	# ----------
	#   Plugin
	# ----------

	def get_files_in_plugin_directories(self, filter: Callable[[str], bool]) -> List[str]:
		result = []
		for plugin_directory in self.mcdr_server.plugin_manager.plugin_directories:
			result.extend(file_util.list_file(plugin_directory, filter))
		return result

	def list_plugin(self, source: CommandSource):
		not_loaded_plugin_list = self.get_files_in_plugin_directories(lambda fp: fp.endswith(constant.PLUGIN_FILE_SUFFIX) and not self.mcdr_server.plugin_manager.contains_plugin_file(fp))  # type: List[str]
		disabled_plugin_list = self.get_files_in_plugin_directories(lambda fp: fp.endswith(constant.DISABLED_PLUGIN_FILE_SUFFIX))  # type: List[str]
		current_plugins = list(self.mcdr_server.plugin_manager.get_all_plugins())  # type: List[AbstractPlugin]

		source.reply(self.tr('mcdr_command.list_plugin.info_loaded_plugin', len(current_plugins)))
		for plugin in current_plugins:
			meta = plugin.get_metadata()
			displayed_name = meta.name.copy()
			if not self.can_see_rtext(source):
				displayed_name += RText(' ({})'.format(plugin.get_identifier()), color=RColor.gray)
			texts = RTextList(
				'§7-§r ',
				displayed_name.
				c(RAction.run_command, '!!MCDR plugin info {}'.format(meta.id)).
				h(self.tr('mcdr_command.list_plugin.suggest_info', meta.id))
			)
			if self.can_see_rtext(source) and not plugin.is_permanent():
				texts.append(
					' ',
					RText('[↻]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin reload {}'.format(meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_reload', meta.id)),
					' ',
					RText('[↓]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin unload {}'.format(meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_unload', meta.id)),
					' ',
					RText('[×]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin disable {}'.format(meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_disable', meta.id))
				)
			source.reply(texts)

		def get_file_name(fp) -> Tuple[str, RText]:
			name = os.path.basename(fp)
			name_text = RText(name)
			if source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
				name_text.h(fp)
			return name, name_text

		source.reply(self.tr('mcdr_command.list_plugin.info_disabled_plugin', len(disabled_plugin_list)))
		for file_path in disabled_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.can_see_rtext(source):
				texts.append(
					' ',
					RText('[✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin enable {}'.format(file_name))
					.h(self.tr('mcdr_command.list_plugin.suggest_enable', file_name))
				)
			source.reply(texts)

		source.reply(self.tr('mcdr_command.list_plugin.info_not_loaded_plugin', len(not_loaded_plugin_list)))
		for file_path in not_loaded_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.can_see_rtext(source):
				texts.append(
					' ',
					RText('[↑]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.tr('mcdr_command.list_plugin.suggest_load', file_name))
				)
			source.reply(texts)

	def show_plugin_info(self, source: CommandSource, plugin_id: str):
		plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
		if plugin is None:
			source.reply(self.tr('mcdr_command.invalid_plugin_id', plugin_id))
		else:
			meta = plugin.get_metadata()
			source.reply(RTextList(
				meta.name.copy().set_color(RColor.yellow).set_styles(RStyle.bold).h(plugin),
				' ',
				RText('v{}'.format(meta.version), color=RColor.gray)
			))
			source.reply('ID: {}'.format(meta.id))
			if meta.author is not None:
				source.reply('Authors: {}'.format(', '.join(meta.author)))
			if meta.link is not None:
				source.reply(RTextList('Link: ', RText(meta.link, color=RColor.blue, styles=RStyle.underlined).c(RAction.open_url, meta.link)))
			if meta.description is not None:
				source.reply(meta.description)

	def __not_loaded_plugin_file_manipulate(self, source: CommandSource, file_name: str, operation_name: str, func: Callable[[str], Any]):
		plugin_paths = self.get_files_in_plugin_directories(lambda fp: os.path.basename(fp) == file_name)
		if len(plugin_paths) == 0:
			source.reply(self.tr('mcdr_command.invalid_plugin_file_name', file_name))
		else:
			result = self.function_call(source, lambda: func(plugin_paths[0]), operation_name, log_success=False, msg_args=(file_name,))
			if result.return_value is True:
				source.reply(self.tr('mcdr_command.{}.success'.format(operation_name), file_name))
			else:
				source.reply(self.tr('mcdr_command.{}.fail'.format(operation_name), file_name))
			self.__print_plugin_operation_result_if_no_error(source, result)

	def __existed_regular_plugin_manipulate(self, source: CommandSource, plugin_id: str, operation_name: str, func: Callable[[RegularPlugin], Any]):
		plugin = self.mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is None or not plugin.is_regular():
			source.reply(self.tr('mcdr_command.invalid_plugin_id', plugin_id))
		else:
			result = self.function_call(source, lambda: func(plugin), operation_name, log_success=False, msg_args=(plugin.get_name(),))
			if result.return_value is True:
				source.reply(self.tr('mcdr_command.{}.success'.format(operation_name), plugin.get_name()))
			else:
				source.reply(self.tr('mcdr_command.{}.fail'.format(operation_name), plugin.get_name()))
			self.__print_plugin_operation_result_if_no_error(source, result)

	def disable_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, 'disable_plugin', lambda plg: self.mcdr_server.server_interface.disable_plugin(plg.get_id(), is_plugin_call=False))

	def reload_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, 'reload_plugin', lambda plg: self.mcdr_server.server_interface.reload_plugin(plg.get_id(), is_plugin_call=False))

	def unload_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, 'unload_plugin', lambda plg: self.mcdr_server.server_interface.unload_plugin(plg.get_id(), is_plugin_call=False))

	def load_plugin(self, source: CommandSource, file_name: str):
		self.__not_loaded_plugin_file_manipulate(source, file_name, 'load_plugin', lambda pth: self.mcdr_server.server_interface.load_plugin(pth, is_plugin_call=False))

	def enable_plugin(self, source: CommandSource, file_name: str):
		self.__not_loaded_plugin_file_manipulate(source, file_name, 'enable_plugin', lambda pth: self.mcdr_server.server_interface.enable_plugin(pth, is_plugin_call=False))

	def reload_all_plugin(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_all_plugins, 'reload_all_plugin', log_success=False)
		self.__print_plugin_operation_result_if_no_error(source, ret)

	# =======================
	#   Help Message things
	# =======================

	def __register_help_messages(self):
		self.register_help_message(HelpMessage(
			self,
			self.get_control_command_prefix(),
			self.plugin_manager.mcdr_server.tr('mcdr_command.help_message.mcdr_command'),
			PermissionLevel.MCDR_CONTROL_LEVEL
		))
		self.register_help_message(HelpMessage(
			self,
			self.get_help_command_prefix(),
			self.plugin_manager.mcdr_server.tr('mcdr_command.help_message.help_command'),
			PermissionLevel.MINIMUM_LEVEL
		))

	def process_help_command(self, source: CommandSource, context: dict):
		page = context.get('page')
		source.reply(self.tr('mcdr_command.help_message.title'))
		matched = []  # type: List[HelpMessage]
		for msg in self.mcdr_server.plugin_manager.registry_storage.help_messages:  # type: HelpMessage
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
				source.reply(RTextList(
					RText(msg.prefix, color=RColor.gray).c(RAction.suggest_command, msg.prefix),
					': ',
					msg.message
				))

		if page is not None:
			has_prev = 0 < left < matched_count
			has_next = 0 < right < matched_count
			color = {False: RColor.dark_gray, True: RColor.gray}
			prev_page = RText('<-', color=color[has_prev])
			if has_prev:
				prev_page.c(RAction.run_command, '!!help {}'.format(page - 1)).h(self.tr('mcdr_command.help_message.previous_page_hover'))
			next_page = RText('->', color=color[has_next])
			if has_next:
				next_page.c(RAction.run_command, '!!help {}'.format(page + 1)).h(self.tr('mcdr_command.help_message.next_page_hover'))

			source.reply(RTextList(
				prev_page,
				' {} '.format(self.tr('mcdr_command.help_message.page_number', page)),
				next_page
			))
