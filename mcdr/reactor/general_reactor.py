"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""
import re

from mcdr.info import InfoSource
from mcdr.permission_manager import PermissionLevel
from mcdr.reactor.abstract_reactor import AbstractReactor
from mcdr.rtext import *


class GeneralReactor(AbstractReactor):
	def react(self, info):
		if info.is_user and re.fullmatch(r'!!MCDR( .*)*', info.content) is not None:
			if self.server.permission_manager.get_info_permission_level(info) >= PermissionLevel.ADMIN:
				self.server.command_manager.process_mcdr_command(info)
			else:
				self.server.server_interface.tell(info.player, RText(self.server.t('general_reactor.permission_denied'), color=RColor.red), is_plugin_call=False)
		else:
			if info.source == InfoSource.CONSOLE and not info.content.startswith(self.server.config['console_command_prefix']):
				self.server.send(info.content)  # send input command to server's stdin

			if info.is_user and info.content == '!!help':
				self.server.command_manager.process_help_command(info)

			self.server.plugin_manager.call('on_info', (self.server.server_interface, info))

			if info.is_user:
				self.server.plugin_manager.call('on_user_info', (self.server.server_interface, info))


def get_reactor(server):
	return GeneralReactor(server)
