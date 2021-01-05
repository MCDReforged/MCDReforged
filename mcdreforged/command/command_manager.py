"""
Handling MCDR commands
"""
import collections
import os
import re
import threading
import traceback
from typing import Callable, Any, List, Tuple, TYPE_CHECKING

from mcdreforged import constant
from mcdreforged.command.builder.command_executor import CommandExecutor
from mcdreforged.command.builder.command_node import Literal, Text, QuotableText
from mcdreforged.command.builder.exception import CommandError, UnknownArgument, RequirementNotMet
from mcdreforged.command.command_source import CommandSource
from mcdreforged.permission_manager import PermissionLevel
from mcdreforged.plugin.plugin import Plugin
from mcdreforged.plugin.plugin_registry import HelpMessage
from mcdreforged.rtext import *
from mcdreforged.server_status import MCDRServerStatus
from mcdreforged.utils import file_util

if TYPE_CHECKING:
	from mcdreforged import MCDReforgedServer


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


# deal with !!MCDR and !!help command
class CommandManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = self.mcdr_server.logger
		self.tr = self.mcdr_server.tr
		self.command_executor = CommandExecutor()

		self.__preserve_command_error_display_flag = False

	# -------------
	#   Interface
	# -------------

	def reset_command(self):
		self.command_executor.clear()
		self.register_mcdr_command()

	def register_command(self, root_node):
		self.command_executor.add_root_node(root_node)

	def execute_command(self, source: CommandSource, command: str):
		command_errors, general_exc_info = self.command_executor.execute(source, command)
		for exc_info in general_exc_info:
			self.logger.error('Error when executing command "{}" with command source "{}"'.format(command, source), exc_info=exc_info)
		for error in command_errors:
			if not error.is_handled():
				source.reply(error.to_mc_color_text())

	# ------------------
	#   Interface ends
	# ------------------

	@staticmethod
	def should_display_buttons(source: CommandSource):
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

	def on_mcdr_command_unknown_argument(self, source: CommandSource, error: CommandError):
		command = error.get_parsed_command()
		source.reply(
			RText(self.tr('command_manager.command_not_found', command)).
			h(self.tr('command_manager.command_not_found_suggest', command)).
			c(RAction.run_command, command)
		)
		error.set_handled()

	def register_mcdr_command(self):
		self.register_command(
			Literal('!!MCDR').
			requires(lambda src: src.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL)).
			runs(
				lambda src: src.reply(self.get_help_message('command_manager.help_message'))
			).
			on_error(RequirementNotMet, lambda src: src.reply(RText(self.mcdr_server.tr('general_reactor.permission_denied'), color=RColor.red))).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
			then(
				Literal({'r', 'reload'}).
				runs(lambda src: src.reply(self.get_help_message('command_manager.help_message_reload'))).
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
				runs(lambda src: src.reply(self.get_help_message('command_manager.help_message_permission'))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
				then(
					Literal('list').runs(lambda src: self.list_permission(src, None)).
					then(Text('level').runs(lambda src, ctx: self.list_permission(src, ctx['level'])))
				).
				then(Literal('set').then(Text('player').then(Text('level').runs(lambda src, ctx: self.set_player_permission(src, ctx['player'], ctx['level']))))).
				then(Literal({'remove', 'rm'}).then(Text('player').runs(lambda src, ctx: self.remove_player_permission(src, ctx['player'])))).
				then(Literal({'setdefault', 'setd'}).then(Text('level').runs(lambda src, ctx: self.remove_player_permission(src, ctx['level']))))
			).
			then(
				Literal({'plugin', 'plg'}).
				runs(lambda src: src.reply(self.get_help_message('command_manager.help_message_plugin'))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
				then(Literal('list').runs(self.list_plugin)).
				then(Literal('load').then(QuotableText('plugin_file').runs(lambda src, ctx: self.load_plugin(src, ctx['plugin_file'])))).
				then(Literal('enable').then(QuotableText('plugin_file').runs(lambda src, ctx: self.enable_plugin(src, ctx['plugin_file'])))).
				then(Literal('reload').then(QuotableText('plugin_id').runs(lambda src, ctx: self.reload_plugin(src, ctx['plugin_id'])))).
				then(Literal('disable').then(QuotableText('plugin_id').runs(lambda src, ctx: self.disable_plugin(src, ctx['plugin_id'])))).
				then(Literal({'reloadall', 'ra'}).runs(self.reload_all_plugin))
			).
			then(
				Literal({'checkupdate', 'cu'}).runs(lambda src: self.mcdr_server.update_helper.check_update(reply_func=src.reply))
			)
		)
		self.register_command(Literal('!!help').runs(self.process_help_command))

	FunctionCallResult = collections.namedtuple('FunctionCallResult', 'return_value no_error')

	def function_call(self, source: CommandSource, func: Callable[[], Any], name: str, log_success=True, log_fail=True, msg_args=()):
		try:
			ret = self.FunctionCallResult(func(), True)
			if log_success:
				source.reply(self.tr('command_manager.{}.success'.format(name), *msg_args))
			return ret
		except:
			if log_fail:
				source.reply(self.tr('command_manager.{}.fail'.format(name), *msg_args))
			self.mcdr_server.logger.error(traceback.format_exc())
			return self.FunctionCallResult(None, False)

	# ----------
	#   Reload
	# ----------

	def refresh_changed_plugins(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', log_success=False)
		if ret.no_error:
			source.reply(self.mcdr_server.plugin_manager.last_operation_result.to_rtext())

	def reload_config(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.load_config, 'reload_config')

	def reload_permission(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.permission_manager.load_permission_file, 'reload_permission')

	def reload_all(self, source: CommandSource):
		self.refresh_changed_plugins(source)
		self.reload_config(source)
		self.reload_permission(source)

	# ----------
	# Permission
	# ----------

	def set_player_permission(self, source: CommandSource, player, value):
		permission_level = PermissionLevel.get_level(value)
		if permission_level is None:
			source.reply(self.tr('command_manager.invalid_permission_level'))
		elif not Validator.player_name(player):
			source.reply(self.tr('command_manager.invalid_player_name'))
		else:
			# Source with permission level x is allowed manipulate players/level in permission level range [0, x]
			if not source.has_permission(max(permission_level.level, self.mcdr_server.permission_manager.get_player_permission_level(player))):
				source.reply(self.tr('command_manager.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.set_permission_level(player, permission_level)
				if source.is_player:
					source.reply(self.tr('permission_manager.set_permission_level.done', player, permission_level.name))

	def remove_player_permission(self, source: CommandSource, player):
		if not Validator.player_name(player):
			source.reply(self.tr('command_manager.invalid_player_name'))
		else:
			if not source.has_permission_higher_than(self.mcdr_server.permission_manager.get_player_permission_level(player)):
				source.reply(self.tr('command_manager.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.remove_player(player)
				source.reply(self.tr('command_manager.remove_player_permission.player_removed', player))

	def list_permission(self, source: CommandSource, target_value):
		specified_level = PermissionLevel.get_level(target_value)
		if specified_level is None:
			# show default level information if target permission not specified
			source.reply(
				RText(self.tr(
					'command_manager.list_permission.show_default',
					self.mcdr_server.permission_manager.get_default_permission_level()
				))
				.c(RAction.suggest_command, '!!MCDR permission setdefault ')
				.h(self.tr('command_manager.list_permission.suggest_setdefault'))
			)
		for permission_level in PermissionLevel.INSTANCES:
			if specified_level is None or permission_level == specified_level:
				source.reply(
					RText('§7[§e{}§7]§r'.format(permission_level.name))
					.c(RAction.run_command, '!!MCDR permission list {}'.format(permission_level.name))
					.h(self.tr('command_manager.list_permission.suggest_list', permission_level.name))
				)
				for player in self.mcdr_server.permission_manager.get_permission_group_list(permission_level.name):
					texts = RText('§7-§r {}'.format(player))
					if self.should_display_buttons(source):
						texts += RTextList(
							RText(' [✎]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission set {} '.format(player))
							.h(self.tr('command_manager.list_permission.suggest_set', player)),
							RText(' [×]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission remove {}'.format(player))
							.h(self.tr('command_manager.list_permission.suggest_disable', player)),
						)
					source.reply(texts)

	def set_default_permission(self, source: CommandSource, value):
		permission_level = PermissionLevel.get_level(value)
		if permission_level is None:
			source.reply(self.tr('command_manager.invalid_permission_level'))
		elif not source.has_permission(permission_level.level):
			source.reply(self.tr('command_manager.permission_not_enough'))
		else:
			self.mcdr_server.permission_manager.set_default_permission_level(permission_level)
			if source.is_player:
				source.reply(self.tr('permission_manager.set_default_permission_level.done', permission_level.name))

	# ------
	# Status
	# ------

	def print_mcdr_status(self, source: CommandSource):
		def bool_formatter(bl):
			return '{}{}§r'.format('§a' if bl else '§7', bl)
		status_dict = {
			True: self.tr('command_manager.print_mcdr_status.online'),
			False: self.tr('command_manager.print_mcdr_status.offline')
		}

		source.reply(RTextList(
			RText(self.tr('command_manager.print_mcdr_status.line1', constant.NAME, constant.VERSION)).c(RAction.open_url, constant.GITHUB_URL).h(RText(constant.GITHUB_URL, styles=RStyle.underlined, color=RColor.blue)), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line2', self.tr(
				MCDRServerStatus.get_translate_key(self.mcdr_server.server_status)))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line3', bool_formatter(self.mcdr_server.is_server_startup()))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line4', bool_formatter(self.mcdr_server.is_exit_naturally()))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line5', status_dict[self.mcdr_server.server_interface.is_rcon_running(is_plugin_call=False)])), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line6', len(self.mcdr_server.plugin_manager.plugins))).c(RAction.suggest_command, '!!MCDR plugin list')
		))
		if source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
			source.reply(RTextList(
				self.tr('command_manager.print_mcdr_status.extra_line1', self.mcdr_server.process.pid if self.mcdr_server.process is not None else '§rN/A§r'), '\n',
				self.tr('command_manager.print_mcdr_status.extra_line2', self.mcdr_server.task_executor.task_queue.qsize(), constant.MAX_TASK_QUEUE_SIZE), '\n',
				self.tr('command_manager.print_mcdr_status.extra_line3', threading.active_count())
			))
			for thread in threading.enumerate():
				source.reply('  §r-§r {}'.format(thread.getName()))

	# ------
	# Plugin
	# ------

	def get_files_in_plugin_folders(self, filter: Callable[[str], bool]) -> List[str]:
		result = []
		for plugin_folder in self.mcdr_server.plugin_manager.plugin_folders:
			result.extend(file_util.list_file(plugin_folder, filter))
		return result

	def list_plugin(self, source: CommandSource):
		not_loaded_plugin_list = self.get_files_in_plugin_folders(lambda fp: fp.endswith(constant.PLUGIN_FILE_SUFFIX) and not self.mcdr_server.plugin_manager.contains_plugin_file(fp))  # type: List[str]
		disabled_plugin_list = self.get_files_in_plugin_folders(lambda fp: fp.endswith(constant.DISABLED_PLUGIN_FILE_SUFFIX))  # type: List[str]
		current_plugins = list(self.mcdr_server.plugin_manager.get_plugins())  # type: List[Plugin]

		source.reply(self.tr('command_manager.list_plugin.info_loaded_plugin', len(current_plugins)))
		for plugin in current_plugins:
			meta = plugin.get_meta_data()
			texts = RTextList('§7-§r ', meta.name.h(str(plugin)))
			if self.should_display_buttons(source):
				texts.append(
					RText(' [×]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin disable {}'.format(meta.id))
					.h(self.tr('command_manager.list_plugin.suggest_disable', meta.id)),
					RText(' [↻]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin reload {}'.format(meta.id))
					.h(self.tr('command_manager.list_plugin.suggest_reload', meta.id))
				)
			source.reply(texts)

		def get_file_name(fp) -> Tuple[str, RText]:
			name = os.path.basename(fp)
			name_text = RText(name)
			if source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
				name_text.h(fp)
			return name, name_text

		source.reply(self.tr('command_manager.list_plugin.info_disabled_plugin', len(disabled_plugin_list)))
		for file_path in disabled_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.should_display_buttons(source):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin enable {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_enable', file_name))
				)
			source.reply(texts)

		source.reply(self.tr('command_manager.list_plugin.info_not_loaded_plugin', len(not_loaded_plugin_list)))
		for file_path in not_loaded_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.should_display_buttons(source):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_load', file_name))
				)
			source.reply(texts)

	def __existed_plugin_manipulate(self, source: CommandSource, plugin_id: str, operation_name: str, func: Callable[[Plugin], Any]):
		plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
		if plugin is None:
			source.reply(self.tr('command_manager.invalid_plugin_id', plugin_id))
		else:
			self.function_call(source, lambda: func(plugin), operation_name, msg_args=(plugin.get_name(),))

	def disable_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_plugin_manipulate(source, plugin_id, 'disable_plugin', self.mcdr_server.plugin_manager.disable_plugin)

	def reload_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_plugin_manipulate(source, plugin_id, 'reload_plugin', self.mcdr_server.plugin_manager.reload_plugin)

	def __not_loaded_plugin_file_manipulate(self, source: CommandSource, file_name: str, operation_name: str, func: Callable[[str], Any]):
		plugin_paths = self.get_files_in_plugin_folders(lambda fp: os.path.basename(fp) == file_name)
		if len(plugin_paths) == 0:
			source.reply(self.tr('command_manager.invalid_plugin_file_name', file_name))
		else:
			plugin_path = plugin_paths[0]
			ret = self.function_call(source, lambda: func(plugin_path), operation_name, log_success=False, msg_args=(file_name,))
			if ret.no_error:  # no outside exception
				source.reply(self.tr('command_manager.{}.{}'.format(operation_name, 'success' if ret.return_value else 'fail'), file_name))

	def load_plugin(self, source: CommandSource, file_name):
		self.__not_loaded_plugin_file_manipulate(source, file_name, 'load_plugin', self.mcdr_server.plugin_manager.load_plugin)

	def enable_plugin(self, source: CommandSource, file_name):
		self.__not_loaded_plugin_file_manipulate(source, file_name, 'enable_plugin', self.mcdr_server.plugin_manager.enable_plugin)

	def reload_all_plugin(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_all_plugins, 'reload_all_plugin', log_success=False)
		if ret.no_error:
			source.reply(self.mcdr_server.plugin_manager.last_operation_result.to_rtext())

	# --------------
	# !!help command
	# --------------

	def process_help_command(self, source: CommandSource):
		for msg in self.mcdr_server.plugin_manager.registry_storage.help_messages:  # type: HelpMessage
			if source.has_permission(msg.permission):
				source.reply(RText('§7{}§r: '.format(msg.prefix)).c(RAction.suggest_command, msg.prefix) + msg.message)
