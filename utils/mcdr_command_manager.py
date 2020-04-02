# -*- coding: utf-8 -*-
import re
import traceback

from utils.info import InfoSource
from utils.permission_manager import PermissionLevel


class Validator:
	@staticmethod
	def player_name(player):
		return re.fullmatch(r'\w{1,16}', player)


class MCDRCommandManager:
	HELP_MESSAGE = '''
!!MCDR: show this message
!!MCDR reload: show reload command help message
!!MCDR status: show MCDR status
!!MCDR permission: show permission command help message
'''.strip()

	HELP_MESSAGE_RELOAD = '''
!!MCDR reload plugin: Reload all plugins 
!!MCDR reload config: Reload config file
!!MCDR reload permission: Reload permission file
!!MCDR reload all: Reload everything above
You can use "r" as a shortform of "reload"
'''.strip()

	HELP_MESSAGE_PERMISSION = '''
!!MCDR permission list [<level>]: list all player's permission. only list permission level [<level>] if [<level>] has set
!!MCDR permission set <player> <level>: set the permission level of <player> to <level>
!!MCDR permission remove <player>: remove <player> from the permission database
You can use "perm" as a shortform of "permission"
'''.strip()

	def __init__(self, server):
		self.server = server
		self.logger = self.server.logger

	def send_message(self, info, msg):
		for line in msg.strip().splitlines():
			if info.source == InfoSource.SERVER:
				self.server.server_interface.tell(info.player, line)
			else:
				self.logger.info(line)

	def process_command(self, info):
		args = info.content.split(' ')
		# !!MCDR
		if len(args) == 1:
			self.send_message(info, self.HELP_MESSAGE)

		# !!MCDR reload
		elif len(args) >= 2 and args[1] in ['r', 'reload']:
			if len(args) == 2:
				self.send_message(info, self.HELP_MESSAGE_RELOAD)
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
					self.send_message(info, 'Command not found, type "!!MCDR reload" to see help')

		# !!MCDR status
		elif len(args) == 2 and args[1] in ['status']:
			self.print_mcdr_status(info)

		# !!MCDR permission <player> <level>
		elif len(args) >= 2 and args[1] in ['permission', 'perm']:
			if len(args) == 2:
				self.send_message(info, self.HELP_MESSAGE_PERMISSION)
			# !!MCDR permission list [<level>]
			elif len(args) in [3, 4] and args[2] == 'list':
				self.list_permission(info, args[3] if len(args) == 4 else None)
			# !!MCDR permission set <player> <level>
			elif len(args) == 5 and args[2] == 'set':
				self.set_player_permission(info, args[3], args[4])
			# !!MCDR permission remove <player>
			elif len(args) == 4 and args[2] == 'remove':
				self.remove_player_permission(info, args[3])
			else:
				self.send_message(info, 'Command not found, type "!!MCDR permission" to see help')

		else:
			self.send_message(info, 'Command not found, type "!!MCDR" to see help')

	# Reload

	def reload_plugins(self, info):
		try:
			msg = self.server.plugin_manager.load_plugins()
		except:
			msg = 'Fail to reload plugin'
			self.server.logger.error(traceback.format_exc())
		self.send_message(info, msg)

	def reload_config(self, info):
		try:
			self.server.load_config()
		except:
			msg = 'Fail to reload config file'
			self.server.logger.error(traceback.format_exc())
		else:
			msg = 'Config file reloaded successfully'
		self.send_message(info, msg)

	def reload_permission(self, info):
		try:
			self.server.permission_manager.load()
		except:
			msg = 'Fail to reload permission file'
			self.server.logger.error(traceback.format_exc())
		else:
			msg = 'Permission file reloaded successfully'
		self.send_message(info, msg)

	def reload_all(self, info):
		self.reload_plugins(info)
		self.reload_config(info)
		self.reload_permission(info)

	# Permission

	def set_player_permission(self, info, player, level):
		level = self.server.permission_manager.format_level_name(level)
		if level is None:
			self.send_message(info, 'Wrong permission level')
		elif not Validator.player_name(player):
			self.send_message(info, 'Wrong player name')
		else:
			self.server.permission_manager.set_level(player, level)
			if info.is_player:
				self.send_message(info, 'The permission level of {0} has set to {1}'.format(player, level))

	def remove_player_permission(self, info, player):
		if not Validator.player_name(player):
			self.send_message(info, 'Wrong player name')
		else:
			self.server.permission_manager.remove_player(player)
			self.send_message(info, 'Player {0} has been removed'.format(player))

	def list_permission(self, info, level):
		specific_name = self.server.permission_manager.format_level_name(level)
		for name in PermissionLevel.NAME:
			if specific_name is None or name == specific_name:
				self.send_message(info, '[{}]'.format(name))
				for player in self.server.permission_manager.get_permission_group_list(name):
					self.send_message(info, '- {}'.format(player))

	# Status

	def print_mcdr_status(self, info):
		msg = 'Server status: {}\nPlugin count: {}'.format(self.server.server_status, len(self.server.plugin_manager.plugins))
		self.send_message(info, msg)
