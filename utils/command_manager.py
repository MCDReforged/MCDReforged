"""
Handling MCDR commands
"""
import collections
import os
import re
import threading
import traceback

from utils import constant, tool
from utils.info import InfoSource
from utils.permission_manager import PermissionLevel
from utils.plugin.plugin import HelpMessage
from utils.rtext import *
from utils.server_status import ServerStatus


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


# deal with !!MCDR and !!help command
class CommandManager:
	def __init__(self, server):
		self.server = server
		self.logger = self.server.logger
		self.t = self.server.t

	def send_message(self, info, msg):
		self.server.server_interface.reply(info, msg, is_plugin_call=False)

	def send_command_not_found(self, info, cmd):
		self.send_message(
			info, RText(self.t('command_manager.command_not_found', cmd))
			.h(self.t('command_manager.command_not_found_suggest', cmd))
			.c(RAction.run_command, cmd)
		)

	def send_help_message(self, info, msg):
		for line in msg.splitlines():
			prefix = re.search(r'(?<=§7)!!MCDR[\w ]*(?=§)', line)
			if prefix is not None:
				self.send_message(info, RText(line).c(RAction.suggest_command, prefix.group()))
			else:
				self.send_message(info, line)

	def display_buttons(self, info):
		return info.source in [InfoSource.SERVER]

	# --------------
	# !!MCDR command
	# --------------

	def process_mcdr_command(self, info):
		args = info.content.split(' ')
		# !!MCDR
		if len(args) == 1:
			self.send_help_message(info, self.t('command_manager.help_message'))

		# !!MCDR reload
		elif len(args) >= 2 and args[1] in ['r', 'reload']:
			if len(args) == 2:
				self.send_help_message(info, self.t('command_manager.help_message_reload'))
			elif len(args) == 3:
				if args[2] in ['plugin', 'plg']:
					self.refresh_changed_plugins(info)
				elif args[2] in ['config', 'cfg']:
					self.reload_config(info)
				elif args[2] in ['permission', 'perm']:
					self.reload_permission(info)
				elif args[2] == 'all':
					self.reload_all(info)
				else:
					self.send_command_not_found(info, '!!MCDR reload')

		# !!MCDR status
		elif len(args) == 2 and args[1] in ['status']:
			self.print_mcdr_status(info)

		# !!MCDR permission
		elif len(args) >= 2 and args[1] in ['permission', 'perm']:
			if len(args) == 2:
				self.send_help_message(info, self.t('command_manager.help_message_permission'))
			# !!MCDR permission list [<level>]
			elif len(args) in [3, 4] and args[2] == 'list':
				self.list_permission(info, args[3] if len(args) == 4 else None)
			# !!MCDR permission set <player> <level>
			elif len(args) == 5 and args[2] == 'set':
				self.set_player_permission(info, args[3], args[4])
			# !!MCDR permission remove <player>
			elif len(args) == 4 and args[2] in ['remove', 'rm']:
				self.remove_player_permission(info, args[3])
			elif len(args) == 4 and args[2] in ['setdefault', 'setd']:
				self.set_default_permission(info, args[3])
			else:
				self.send_command_not_found(info, '!!MCDR permission')

		# !!MCDR plugin
		elif len(args) >= 2 and args[1] in ['plugin', 'plg']:
			if len(args) == 2:
				self.send_help_message(info, self.t('command_manager.help_message_plugin'))
			elif len(args) == 3 and args[2] in ['list']:
				self.list_plugin(info)
			elif len(args) == 4 and args[2] in ['load']:
				self.load_plugin(info, args[3])
			elif len(args) == 4 and args[2] in ['disable']:
				self.disable_plugin(info, args[3])
			elif len(args) == 4 and args[2] in ['enable']:
				self.enable_plugin(info, args[3])
			elif len(args) == 3 and args[2] in ['reloadall', 'ra']:
				self.reload_all_plugin(info)
			else:
				self.send_command_not_found(info, '!!MCDR plugin')

		# !!MCDR checkupdate
		elif len(args) == 2 and args[1] in ['cu', 'checkupdate']:
			def reply(msg):
				self.send_message(info, msg)
			self.server.update_helper.check_update(reply_func=reply)

		else:
			self.send_command_not_found(info, '!!MCDR')

	def function_call(self, info, func, name, func_args=(), success_message=True, fail_message=True, message_args=()):
		try:
			ret = collections.namedtuple('Result', 'return_value')(func(*func_args))
			if success_message:
				self.send_message(info, self.t('command_manager.{}.success'.format(name), *message_args))
			return ret
		except:
			if fail_message:
				self.send_message(info, self.t('command_manager.{}.fail'.format(name), *message_args))
			self.server.logger.error(traceback.format_exc())
			return None

	# ------
	# Reload
	# ------

	def refresh_changed_plugins(self, info):
		ret = self.function_call(info, self.server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', success_message=False)
		if ret is not None:
			self.send_message(info, ret.return_value)

	def reload_config(self, info):
		self.function_call(info, self.server.load_config, 'reload_config')

	def reload_permission(self, info):
		self.function_call(info, self.server.permission_manager.load, 'reload_permission')

	def reload_all(self, info):
		self.refresh_changed_plugins(info)
		self.reload_config(info)
		self.reload_permission(info)

	# ----------
	# Permission
	# ----------

	def set_player_permission(self, info, player, level):
		level = self.server.permission_manager.format_level_name(level)
		if level is None:
			self.send_message(info, self.t('command_manager.invalid_permission_level'))
		elif not Validator.player_name(player):
			self.send_message(info, self.t('command_manager.invalid_player_name'))
		else:
			executor_level = self.server.permission_manager.get_info_permission_level(info)
			if max(self.server.permission_manager.format_level_value(level), self.server.permission_manager.get_player_permission_level(player)) > executor_level:
				self.send_message(info, self.t('command_manager.permission_not_enough'))
			else:
				self.server.permission_manager.set_permission_level(player, level)
				if info.is_player:
					self.send_message(info, self.t('permission_manager.set_permission_level.done', player, level))

	def remove_player_permission(self, info, player):
		if not Validator.player_name(player):
			self.send_message(info, self.t('command_manager.invalid_player_name'))
		else:
			if self.server.permission_manager.get_player_permission_level(player) > self.server.permission_manager.get_info_permission_level(info):
				self.send_message(info, self.t('command_manager.permission_not_enough'))
			else:
				self.server.permission_manager.remove_player(player)
				self.send_message(info, self.t('command_manager.remove_player_permission.player_removed', player))

	def list_permission(self, info, level):
		specific_name = self.server.permission_manager.format_level_name(level)
		if specific_name is None:
			self.send_message(
				info, RText(self.t(
					'command_manager.list_permission.show_default',
					self.server.permission_manager.get_default_permission_level()
				))
				.c(RAction.suggest_command, '!!MCDR permission setdefault ')
				.h(self.t('command_manager.list_permission.suggest_setdefault'))
			)
		for name in PermissionLevel.NAME:
			if specific_name is None or name == specific_name:
				self.send_message(
					info, RText('§7[§e{}§7]§r'.format(name))
					.c(RAction.run_command, '!!MCDR permission list {}'.format(name))
					.h(self.t('command_manager.list_permission.suggest_list', name))
				)
				for player in self.server.permission_manager.get_permission_group_list(name):
					texts = RText('§7-§r {}'.format(player))
					if self.display_buttons(info):
						texts += RTextList(
							RText(' [✎]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission set {} '.format(player))
							.h(self.t('command_manager.list_permission.suggest_set', player)),
							RText(' [×]', color=RColor.gray)
							.c(RAction.suggest_command, '!!MCDR permission remove {}'.format(player))
							.h(self.t('command_manager.list_permission.suggest_disable', player)),
						)
					self.send_message(info, texts)

	def set_default_permission(self, info, level):
		level = self.server.permission_manager.format_level_name(level)
		if level is None:
			self.send_message(info, self.t('command_manager.invalid_permission_level'))
		elif self.server.permission_manager.format_level_value(level) > self.server.permission_manager.get_info_permission_level(info):
			self.send_message(info, self.t('command_manager.permission_not_enough'))
		else:
			self.server.permission_manager.set_default_permission_level(level)
			if info.is_player:
				self.send_message(info, self.t('permission_manager.set_default_permission_level.done', level))

	# ------
	# Status
	# ------

	def print_mcdr_status(self, info):
		def bool_formatter(bl):
			return '{}{}§r'.format('§a' if bl else '§7', bl)
		status_dict = {
			True: self.t('command_manager.print_mcdr_status.online'),
			False: self.t('command_manager.print_mcdr_status.offline')
		}

		self.send_message(info, RTextList(
			RText(self.t('command_manager.print_mcdr_status.line1', constant.NAME, constant.VERSION)).c(RAction.open_url, constant.GITHUB_URL).h(RText(constant.GITHUB_URL, styles=RStyle.underlined, color=RColor.blue)), '\n',
			RText(self.t('command_manager.print_mcdr_status.line2', self.t(ServerStatus.translate_key(self.server.server_status)))), '\n',
			RText(self.t('command_manager.print_mcdr_status.line3', bool_formatter(self.server.is_server_startup()))), '\n',
			RText(self.t('command_manager.print_mcdr_status.line4', bool_formatter(self.server.is_exit_naturally()))), '\n',
			RText(self.t('command_manager.print_mcdr_status.line5', status_dict[self.server.server_interface.is_rcon_running(is_plugin_call=False)])), '\n',
			RText(self.t('command_manager.print_mcdr_status.line6', len(self.server.plugin_manager.plugins))).c(RAction.suggest_command, '!!MCDR plugin list')
		))
		if self.server.permission_manager.get_info_permission_level(info) >= PermissionLevel.OWNER:
			self.send_message(info, RTextList(
				self.t('command_manager.print_mcdr_status.extra_line1', self.server.process.pid if self.server.process is not None else '§rN/A§r'), '\n',
				self.t('command_manager.print_mcdr_status.extra_line2', self.server.reactor_manager.info_queue.qsize(), constant.MAX_INFO_QUEUE_SIZE), '\n',
				self.t('command_manager.print_mcdr_status.extra_line3', threading.active_count())
			))
			for thread in threading.enumerate():
				self.send_message(info, '  §r-§r {}'.format(thread.getName()))

	# ------
	# Plugin
	# ------

	def list_plugin(self, info):
		file_list_all = self.server.plugin_manager.get_plugin_file_list_all()
		file_list_disabled = self.server.plugin_manager.get_plugin_file_list_disabled()
		file_list_loaded = self.server.plugin_manager.get_loaded_plugin_file_name_list()
		file_list_not_loaded = [file_name for file_name in file_list_all if file_name not in file_list_loaded]

		self.send_message(info, self.t('command_manager.list_plugin.info_loaded_plugin', len(file_list_loaded)))
		for file_name in file_list_loaded:
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.display_buttons(info):
				texts.append(
					RText(' [×]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin disable {}'.format(file_name))
					.h(self.t('command_manager.list_plugin.suggest_disable', file_name)),
					RText(' [↻]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.t('command_manager.list_plugin.suggest_reload', file_name))
				)
			self.send_message(info, texts)

		self.send_message(info, self.t('command_manager.list_plugin.info_disabled_plugin', len(file_list_disabled)))
		for file_name in file_list_disabled:
			file_name = tool.remove_suffix(file_name, constant.DISABLED_PLUGIN_FILE_SUFFIX)
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.display_buttons(info):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin enable {}'.format(file_name))
					.h(self.t('command_manager.list_plugin.suggest_enable', file_name))
				)
			self.send_message(info, texts)

		self.send_message(info, self.t('command_manager.list_plugin.info_not_loaded_plugin', len(file_list_not_loaded)))
		for file_name in file_list_not_loaded:
			texts = RTextList('§7-§r {}'.format(file_name))
			if self.display_buttons(info):
				texts.append(
					RText(' [✔]', color=RColor.gray)
					.c(RAction.run_command, '!!MCDR plugin load {}'.format(file_name))
					.h(self.t('command_manager.list_plugin.suggest_load', file_name))
				)
			self.send_message(info, texts)

	def disable_plugin(self, info, file_name):
		file_name = tool.format_plugin_file_name(file_name)
		if not os.path.isfile(os.path.join(self.server.plugin_manager.plugin_folder, file_name)):
			self.send_message(info, self.t('command_manager.invalid_plugin_name', file_name))
		else:
			self.function_call(info, self.server.plugin_manager.disable_plugin, 'disable_plugin', func_args=(file_name, ), message_args=(file_name, ))

	def load_plugin(self, info, file_name):
		file_name = tool.format_plugin_file_name(file_name)
		if not os.path.isfile(os.path.join(self.server.plugin_manager.plugin_folder, file_name)):
			self.send_message(info, self.t('command_manager.invalid_plugin_name', file_name))
		else:
			ret = self.function_call(
				info, self.server.plugin_manager.load_plugin, 'load_plugin',
				func_args=(file_name, ), message_args=(file_name, ), success_message=False
			)
			if ret is not None:  # no outside exception
				self.send_message(info, self.t('command_manager.load_plugin.{}'.format('success' if ret.return_value else 'fail'), file_name))

	def enable_plugin(self, info, file_name):
		file_name = tool.format_plugin_file_name_disabled(file_name)
		if not os.path.isfile(os.path.join(self.server.plugin_manager.plugin_folder, file_name)):
			self.send_message(info, self.t('command_manager.invalid_plugin_name', file_name))
		else:
			ret = self.function_call(
				info, self.server.plugin_manager.enable_plugin, 'enable_plugin',
				func_args=(file_name, ), message_args=(file_name, ), success_message=False
			)
			if ret is not None:  # no outside exception
				if ret.return_value:
					message = self.t('command_manager.enable_plugin.success', file_name)
				else:
					message = self.t('command_manager.load_plugin.fail', file_name)
				self.send_message(info, message)

	def reload_all_plugin(self, info):
		ret = self.function_call(info, self.server.plugin_manager.refresh_all_plugins, 'reload_all_plugin', success_message=False)
		if ret is not None:
			self.send_message(info, ret.return_value)

	# --------------
	# !!help command
	# --------------

	def process_help_command(self, info):
		help_messages = [HelpMessage('!!MCDR', self.t('command_manager.mcdr_help_message'), RText('MCDR', color=RColor.gold))]
		for plugin in self.server.plugin_manager.plugins:
			help_messages.extend(plugin.help_messages)
		for prefix, message, name in sorted(help_messages, key=lambda x: x.prefix.upper()):
			self.send_message(info, RText('§7{}§r: '.format(prefix)).c(RAction.suggest_command, prefix).h(name) + message)
