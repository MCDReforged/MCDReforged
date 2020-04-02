# -*- coding: utf-8 -*-
import re

from utils.info import InfoSource
from utils.mcdr_command_manager import MCDRCommandManager
from utils.permission_manager import PermissionLevel
from utils.reactor.base_reactor import BaseReactor


class GeneralReactor(BaseReactor):
	def __init__(self, server):
		super().__init__(server)
		self.command_manager = MCDRCommandManager(server)

	def react(self, info):
		if info.is_user and re.fullmatch(r'!!MCDR( .*)*', info.content) is not None:
			if self.server.permission_manager.get_info_level(info) == PermissionLevel.ADMIN:
				self.command_manager.process_command(info)
			else:
				self.server.server_interface.tell(info.player, '§cPermission denied§r')
		else:
			if info.source == InfoSource.CONSOLE and not info.content.startswith(self.server.config['console_command_prefix']):
				self.server.send(info.content)  # send input command to server's stdin
			self.server.plugin_manager.call('on_info', (self.server.server_interface, info))


def get_reactor(server):
	return GeneralReactor(server)

