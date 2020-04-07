# -*- coding: utf-8 -*-
import re
import traceback

from utils import constant, tool
from utils.info import InfoSource
from utils.permission_manager import PermissionLevel


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


class MCDRCommandManager:
	def __init__(self, server):
		self.server = server
		self.logger = self.server.logger

	def send_message(self, info, msg):
		for line in msg.strip().splitlines():
			if info.source == InfoSource.SERVER:
				self.server.server_interface.tell(info.player, line, is_plugin_call=False)
			else:
				self.logger.info(tool.clean_minecraft_color_code(line))

	def process_command(self, info):
		args = info.content.rstrip().split(' ')
		# !!MCDR
		if len(args) == 1:
			self.send_message(info, self.server.t('mcdr_command_manager.help_message'))

		# !!MCDR reload
		elif len(args) >= 2 and args[1] in ['r', 'reload']:
			if len(args) == 2:
				self.send_message(info, self.server.t('mcdr_command_manager.help_message_reload'))
			elif len(args) == 3:
				if args[2] in ['plugin', 'plg']:
					self.reload_plugins(info)
				elif args[2] in ['config', 'cfg']:
					self.reload_config(info)
				elif args[2] in ['permission', 'perm']:
					self.reload_permission(info)
				elif args[2] == 'all':
					self.reload_all(info)
				else:
					self.send_message(info, self.server.t('mcdr_command_manager.command_not_found', '!!MCDR reload'))

		# !!MCDR status
		elif len(args) == 2 and args[1] in ['status']:
			self.print_mcdr_status(info)

		# !!MCDR permission <player> <level>
		elif len(args) >= 2 and args[1] in ['permission', 'perm']:
			if len(args) == 2:
				self.send_message(info, self.server.t('mcdr_command_manager.help_message_permission'))
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
				self.send_message(info, self.server.t('mcdr_command_manager.command_not_found', '!!MCDR permission'))

		else:
			self.send_message(info, self.server.t('mcdr_command_manager.command_not_found', '!!MCDR'))

	# Reload

	def reload_plugins(self, info):
		try:
			msg = self.server.plugin_manager.load_plugins()
		except:
			msg = self.server.t('mcdr_command_manager.reload_plugins.load_fail')
			self.server.logger.error(traceback.format_exc())
		self.send_message(info, msg)

	def reload_config(self, info):
		try:
			self.server.load_config()
		except:
			msg = self.server.t('mcdr_command_manager.reload_config.load_fail')
			self.server.logger.error(traceback.format_exc())
		else:
			msg = self.server.t('mcdr_command_manager.reload_config.load_success')
		self.send_message(info, msg)

	def reload_permission(self, info):
		try:
			self.server.permission_manager.load()
		except:
			msg = self.server.t('mcdr_command_manager.reload_permission.load_fail')
			self.server.logger.error(traceback.format_exc())
		else:
			msg = self.server.t('mcdr_command_manager.reload_permission.load_success')
		self.send_message(info, msg)

	def reload_all(self, info):
		self.reload_plugins(info)
		self.reload_config(info)
		self.reload_permission(info)

	# Permission

	def set_player_permission(self, info, player, level):
		level = self.server.permission_manager.format_level_name(level)
		if level is None:
			self.send_message(info, self.server.t('mcdr_command_manager.invalid_permission_level'))
		elif not Validator.player_name(player):
			self.send_message(info, self.server.t('mcdr_command_manager.invalid_player_name'))
		else:
			self.server.permission_manager.set_permission_level(player, level)
			if info.is_player:
				self.send_message(info, self.server.t('permission_manager.set_permission_level.done', player, level))

	def remove_player_permission(self, info, player):
		if not Validator.player_name(player):
			self.send_message(info, self.server.t('mcdr_command_manager.invalid_player_name'))
		else:
			self.server.permission_manager.remove_player(player)
			self.send_message(info, self.server.t('mcdr_command_manager.remove_player_permission.player_removed', player))

	def list_permission(self, info, level):
		self.send_message(info, self.server.t('mcdr_command_manager.list_permission.show_default',
			self.server.permission_manager.get_default_permission_level()))
		specific_name = self.server.permission_manager.format_level_name(level)
		for name in PermissionLevel.NAME:
			if specific_name is None or name == specific_name:
				self.send_message(info, '§7[§e{}§7]§r'.format(name))
				for player in self.server.permission_manager.get_permission_group_list(name):
					self.send_message(info, '§7-§r {}'.format(player))

	def set_default_permission(self, info, level):
		level = self.server.permission_manager.format_level_name(level)
		if level is None:
			self.send_message(info, self.server.t('mcdr_command_manager.invalid_permission_level'))
		else:
			self.server.permission_manager.set_default_permission_level(level)
			if info.is_player:
				self.send_message(info, self.server.t('permission_manager.set_default_permission_level.done', level))

	# Status

	def print_mcdr_status(self, info):
		status_dict = {
			True: self.server.t('mcdr_command_manager.print_mcdr_status.online'),
			False: self.server.t('mcdr_command_manager.print_mcdr_status.offline')
		}
		msg = []
		msg.append(self.server.t('mcdr_command_manager.print_mcdr_status.line1', constant.NAME, constant.VERSION))
		msg.append(self.server.t('mcdr_command_manager.print_mcdr_status.line2', self.server.t(self.server.server_status)))
		msg.append(self.server.t('mcdr_command_manager.print_mcdr_status.line3', self.server.is_server_startup()))
		msg.append(self.server.t('mcdr_command_manager.print_mcdr_status.line4', status_dict[self.server.server_interface.is_rcon_running(is_plugin_call=False)]))
		msg.append(self.server.t('mcdr_command_manager.print_mcdr_status.line5', len(self.server.plugin_manager.plugins)))
		self.send_message(info, '\n'.join(msg))
		if info.source == InfoSource.CONSOLE and self.server.process is not None:
			self.logger.info('PID: {}'.format(self.server.process.pid))
