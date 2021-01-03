"""
Handling MCDR commands
"""
import collections
import os
import re
import threading
import traceback

from mcdr import constant
from mcdr.command.builder.command_executor import CommandExecutor
from mcdr.command.builder.command_node import Literal, Text, QuotableText
from mcdr.command.builder.exception import CommandError, UnknownArgument, PermissionDenied
from mcdr.command.command_source import CommandSource
from mcdr.logger import Logger
from mcdr.permission_manager import PermissionLevel
from mcdr.plugin.plugin_registry import HelpMessage
from mcdr.rtext import *
from mcdr.server_status import ServerStatus
from mcdr.utils import string_util


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


# deal with !!MCDR and !!help command
class CommandManager:
	def __init__(self, mcdr_server):
		self.mcdr_server = mcdr_server
		self.logger = self.mcdr_server.logger  # type: Logger
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
		try:
			command_errors = self.command_executor.execute(source, command)
		except:
			self.logger.exception('Error when executing command "{}" with command source "{}"'.format(command, source))
		else:
			if not self.__preserve_command_error_display_flag:
				for error in command_errors:
					source.reply(error.to_mc_color_text())
				self.__preserve_command_error_display_flag = False

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
		self.__preserve_command_error_display_flag = True

	def register_mcdr_command(self):
		executor = Literal('!!MCDR').\
			requires(lambda src: src.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL)).\
			runs(
				lambda src, ctx: src.reply(self.get_help_message('command_manager.help_message'))
			).\
			then(
				Literal({'r', 'reload'}).
				runs(lambda src, ctx: src.reply(self.get_help_message('command_manager.help_message_reload'))).
				then(Literal({'plugin', 'plg'}).runs(lambda src, ctx: self.refresh_changed_plugins(src))).
				then(Literal({'config', 'cfg'}).runs(lambda src, ctx: self.reload_config(src))).
				then(Literal({'permission', 'perm'}).runs(lambda src, ctx: self.reload_permission(src))).
				then(Literal('all').runs(lambda src, ctx: self.reload_all(src))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument)
			).\
			then(
				Literal('status').runs(lambda src, ctx: self.print_mcdr_status(src))
			).\
			then(
				Literal({'permission', 'perm'}).
				runs(lambda src, ctx: src.reply(self.get_help_message('command_manager.help_message_permission'))).
				then(
					Literal('list').runs(lambda src, ctx: self.list_permission(src, None)).
					then(Text('level').runs(lambda src, ctx: self.list_permission(src, ctx['level'])))
				).
				then(Literal('set').then(Text('player').then(Text('level').runs(lambda src, ctx: self.set_player_permission(src, ctx['player'], ctx['level']))))).
				then(Literal({'remove', 'rm'}).then(Text('player').runs(lambda src, ctx: self.remove_player_permission(src, ctx['player'])))).
				then(Literal({'setdefault', 'setd'}).then(Text('level').runs(lambda src, ctx: self.remove_player_permission(src, ctx['level'])))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument)
			).\
			then(
				Literal({'plugin', 'plg'}).
				runs(lambda src, ctx: src.reply(self.get_help_message('command_manager.help_message_plugin'))).
				then(Literal('list').runs(lambda src, ctx: self.list_plugin(src))).
				then(Literal('load').then(QuotableText('plugin').runs(lambda src, ctx: self.load_plugin(src, ctx['plugin'])))).
				then(Literal('disable').then(QuotableText('plugin').runs(lambda src, ctx: self.disable_plugin(src, ctx['plugin'])))).
				then(Literal('enable').then(QuotableText('plugin').runs(lambda src, ctx: self.enable_plugin(src, ctx['plugin'])))).
				then(Literal({'reloadall', 'ra'}).runs(lambda src, ctx: self.reload_all_plugin(src))).
				on_error(UnknownArgument, self.on_mcdr_command_unknown_argument)
			).\
			then(
				Literal({'checkupdate', 'cu'}).runs(lambda src, ctx: self.mcdr_server.update_helper.check_update(reply_func=src.reply))
			).\
			on_error(PermissionDenied, lambda src, ctx: src.reply(RText(self.mcdr_server.tr('general_reactor.permission_denied'), color=RColor.red))).\
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument)
		self.register_command(executor)

	# ------
	# Reload
	# ------

	def function_call(self, source: CommandSource, func, name, func_args=(), success_message=True, fail_message=True, message_args=()):
		try:
			ret = collections.namedtuple('Result', 'return_value')(func(*func_args))
			if success_message:
				source.reply(self.tr('command_manager.{}.success'.format(name), *message_args))
			return ret
		except:
			if fail_message:
				source.reply(self.tr('command_manager.{}.fail'.format(name), *message_args))
			self.mcdr_server.logger.error(traceback.format_exc())
			return None

	def refresh_changed_plugins(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', success_message=False)
		if ret is not None:
			source.reply(ret.return_value)

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

	def set_player_permission(self, source: CommandSource, player, level):
		level = self.mcdr_server.permission_manager.format_level_name(level)
		if level is None:
			source.reply(self.tr('command_manager.invalid_permission_level'))
		elif not Validator.player_name(player):
			source.reply(self.tr('command_manager.invalid_player_name'))
		else:
			if not source.has_permission_higher_than(max(self.mcdr_server.permission_manager.format_level_value(level), self.mcdr_server.permission_manager.get_player_permission_level(player))):
				source.reply(self.tr('command_manager.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.set_permission_level(player, level)
				if source.is_player:
					source.reply(self.tr('permission_manager.set_permission_level.done', player, level))

	def remove_player_permission(self, source: CommandSource, player):
		if not Validator.player_name(player):
			source.reply(self.tr('command_manager.invalid_player_name'))
		else:
			if not source.has_permission_higher_than(self.mcdr_server.permission_manager.get_player_permission_level(player)):
				source.reply(self.tr('command_manager.permission_not_enough'))
			else:
				self.mcdr_server.permission_manager.remove_player(player)
				source.reply(self.tr('command_manager.remove_player_permission.player_removed', player))

	def list_permission(self, source: CommandSource, level):
		specific_name = self.mcdr_server.permission_manager.format_level_name(level)
		if specific_name is None:
			source.reply(
				RText(self.tr(
					'command_manager.list_permission.show_default',
					self.mcdr_server.permission_manager.get_default_permission_level()
				))
				.c(RAction.suggest_command, '!!MCDR permission setdefault ')
				.h(self.tr('command_manager.list_permission.suggest_setdefault'))
			)
		for name in PermissionLevel.NAME:
			if specific_name is None or name == specific_name:
				source.reply(
					RText('§7[§e{}§7]§r'.format(name))
					.c(RAction.run_command, '!!MCDR permission list {}'.format(name))
					.h(self.tr('command_manager.list_permission.suggest_list', name))
				)
				for player in self.mcdr_server.permission_manager.get_permission_group_list(name):
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

	def set_default_permission(self, source: CommandSource, level):
		level = self.mcdr_server.permission_manager.format_level_name(level)
		if level is None:
			source.reply(self.tr('command_manager.invalid_permission_level'))
		elif not source.has_permission(self.mcdr_server.permission_manager.format_level_value(level)):
			source.reply(self.tr('command_manager.permission_not_enough'))
		else:
			self.mcdr_server.permission_manager.set_default_permission_level(level)
			if source.is_player:
				source.reply(self.tr('permission_manager.set_default_permission_level.done', level))

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
				ServerStatus.get_translate_key(self.mcdr_server.mcdr_server_status)))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line3', bool_formatter(self.mcdr_server.is_server_startup()))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line4', bool_formatter(self.mcdr_server.is_exit_naturally()))), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line5', status_dict[self.mcdr_server.server_interface.is_rcon_running(is_plugin_call=False)])), '\n',
			RText(self.tr('command_manager.print_mcdr_status.line6', len(self.mcdr_server.plugin_manager.plugins))).c(RAction.suggest_command, '!!MCDR plugin list')
		))
		if source.has_permission(PermissionLevel.OWNER):
			source.reply(RTextList(
				self.tr('command_manager.print_mcdr_status.extra_line1', self.mcdr_server.process.pid if self.mcdr_server.process is not None else '§rN/A§r'), '\n',
				self.tr('command_manager.print_mcdr_status.extra_line2', self.mcdr_server.reactor_manager.info_queue.qsize(), constant.MAX_INFO_QUEUE_SIZE), '\n',
				self.tr('command_manager.print_mcdr_status.extra_line3', threading.active_count())
			))
			for thread in threading.enumerate():
				source.reply('  §r-§r {}'.format(thread.getName()))

	# ------
	# Plugin
	# ------

	def list_plugin(self, source: CommandSource):
		file_list_all = self.mcdr_server.plugin_manager.get_plugin_file_list_all()
		file_list_disabled = self.mcdr_server.plugin_manager.get_plugin_file_list_disabled()
		file_list_loaded = self.mcdr_server.plugin_manager.get_loaded_plugin_file_name_list()
		file_list_not_loaded = [file_name for file_name in file_list_all if file_name not in file_list_loaded]

		source.reply(self.tr('command_manager.list_plugin.info_loaded_plugin', len(file_list_loaded)))
		for file_name in file_list_loaded:
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.should_display_buttons(source):
				texts.append(
					RText(' [×]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin disable {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_disable', file_name)),
					RText(' [↻]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_reload', file_name))
				)
			source.reply(texts)

		source.reply(self.tr('command_manager.list_plugin.info_disabled_plugin', len(file_list_disabled)))
		for file_name in file_list_disabled:
			file_name = string_util.remove_suffix(file_name, constant.DISABLED_PLUGIN_FILE_SUFFIX)
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.should_display_buttons(source):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin enable {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_enable', file_name))
				)
			source.reply(texts)

		source.reply(self.tr('command_manager.list_plugin.info_not_loaded_plugin', len(file_list_not_loaded)))
		for file_name in file_list_not_loaded:
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.should_display_buttons(source):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.tr('command_manager.list_plugin.suggest_load', file_name))
				)
			source.reply(texts)

	def disable_plugin(self, source: CommandSource, file_name):
		file_name = string_util.format_plugin_file_name(file_name)
		if not os.path.isfile(os.path.join(self.mcdr_server.plugin_manager.plugin_folder, file_name)):
			source.reply(self.tr('command_manager.invalid_plugin_name', file_name))
		else:
			self.function_call(source, self.mcdr_server.plugin_manager.disable_plugin, 'disable_plugin', func_args=(file_name, ), message_args=(file_name, ))

	def load_plugin(self, source: CommandSource, file_name):
		file_name = string_util.format_plugin_file_name(file_name)
		if not os.path.isfile(os.path.join(self.mcdr_server.plugin_manager.plugin_folder, file_name)):
			source.reply(self.tr('command_manager.invalid_plugin_name', file_name))
		else:
			ret = self.function_call(
				source, self.mcdr_server.plugin_manager.load_plugin, 'load_plugin',
				func_args=(file_name, ), message_args=(file_name, ), success_message=False
			)
			if ret is not None:  # no outside exception
				source.reply(self.tr('command_manager.load_plugin.{}'.format('success' if ret.return_value else 'fail'), file_name))

	def enable_plugin(self, source: CommandSource, file_name):
		file_name = string_util.format_plugin_file_name_disabled(file_name)
		if not os.path.isfile(os.path.join(self.mcdr_server.plugin_manager.plugin_folder, file_name)):
			source.reply(self.tr('command_manager.invalid_plugin_name', file_name))
		else:
			ret = self.function_call(
				source, self.mcdr_server.plugin_manager.enable_plugin, 'enable_plugin',
				func_args=(file_name, ), message_args=(file_name, ), success_message=False
			)
			if ret is not None:  # no outside exception
				if ret.return_value:
					message = self.tr('command_manager.enable_plugin.success', file_name)
				else:
					message = self.tr('command_manager.load_plugin.fail', file_name)
				source.reply(message)

	def reload_all_plugin(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_all_plugins, 'reload_all_plugin', success_message=False)
		if ret is not None:
			source.reply(ret.return_value)

	# --------------
	# !!help command
	# --------------

	def process_help_command(self, source: CommandSource):
		for msg in self.mcdr_server.plugin_manager.registry_storage.help_messages:  # type: HelpMessage
			# TODO: permission check
			source.reply(RText('§7{}§r: '.format(msg.prefix)).c(RAction.suggest_command, msg.prefix) + msg.message)
