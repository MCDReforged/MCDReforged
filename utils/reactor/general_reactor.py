# -*- coding: utf-8 -*-
import re
import traceback

from utils.info import InfoSource
from utils.permission_manager import PermissionLevel
from utils.reactor.base_reactor import BaseReactor


class GeneralReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.is_user and re.fullmatch(r'!!MCDR( .*)*', info.content) is not None:
			if server.permission_manager.get_info_level(info) == PermissionLevel.ADMIN:
				MCDRCommandManager.process_command(server, info)
			else:
				server.server_interface.tell(info.player, '§cPermission denied§r')
		else:
			if info.source == InfoSource.CONSOLE:  # send input command to server's stdin
				server.send(info.content)
			server.plugin_manager.call('on_info', (server.server_interface, info))


reactor = GeneralReactor


class MCDRCommandManager:
	HELP_MESSAGE = '''
!!MCDR: show this message
!!MCDR reload: show reload command help message
!!MCDR status: show MCDR status
'''.strip()
	HELP_MESSAGE_RELOAD = '''
!!MCDR reload plugin: Reload all plugins 
!!MCDR reload config: Reload config file
!!MCDR reload permission: Reload permission file
!!MCDR reload all: Reload everything above
'''.strip()

	@staticmethod
	def send_message(server, info, msg):
		for line in msg.strip().splitlines():
			if info.source == InfoSource.SERVER:
				server.server_interface.tell(info.player, line)
			else:
				server.logger.info(line)

	@staticmethod
	def process_command(server, info):
		args = info.content.split(' ')
		if len(args) == 1:
			MCDRCommandManager.send_message(server, info, MCDRCommandManager.HELP_MESSAGE)
		elif len(args) >= 2 and args[1] in ['r', 'reload']:
			if len(args) == 2:
				MCDRCommandManager.send_message(server, info, MCDRCommandManager.HELP_MESSAGE_RELOAD)
			elif len(args) == 3:
				if args[2] in ['plugin', 'plg']:
					MCDRCommandManager.reload_plugins(server, info)
				elif args[2] in ['config', 'cfg']:
					MCDRCommandManager.reload_config(server, info)
				elif args[2] in ['permission', 'perm']:
					MCDRCommandManager.reload_permission(server, info)
				elif args[2] == 'all':
					MCDRCommandManager.reload_all(server, info)
		elif len(args) == 2 and args[1] in ['status']:
			msg = 'Server status: {}\nPlugin count: {}'.format(server.server_status, len(server.plugin_manager.plugins))
			MCDRCommandManager.send_message(server, info, msg)

	@staticmethod
	def reload_plugins(server, info):
		msg = server.plugin_manager.load_plugins()
		if server.is_running():
			server.server_interface.say(msg)

	@staticmethod
	def reload_config(server, info):
		try:
			server.load_config()
		except:
			msg = 'Fail to reload config file'
			server.logger.error(traceback.format_exc())
		else:
			msg = 'Config file reloaded successfully'
		server.logger.info(msg)

	@staticmethod
	def reload_permission(server, info):
		try:
			server.permission_manager.load()
		except:
			msg = 'Fail to reload permission file'
			server.logger.error(traceback.format_exc())
		else:
			msg = 'Permission file reloaded successfully'
		server.logger.info(msg)

	@staticmethod
	def reload_all(server, info):
		MCDRCommandManager.reload_plugins(server, info)
		MCDRCommandManager.reload_config(server, info)
		MCDRCommandManager.reload_permission(server, info)

