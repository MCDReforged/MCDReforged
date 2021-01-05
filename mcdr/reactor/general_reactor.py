"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""

from mcdr.info import InfoSource
from mcdr.plugin.plugin_event import PluginEvents
from mcdr.reactor.abstract_reactor import AbstractReactor


class GeneralReactor(AbstractReactor):
	def react(self, info):
		if info.is_user:
			self.mcdr_server.command_manager.execute_command(info.to_command_source(), info.content)

		if info.source == InfoSource.CONSOLE and not info.content.startswith(self.mcdr_server.config['console_command_prefix']):
			self.mcdr_server.send(info.content)  # send input command to server's stdin

		self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.GENERAL_INFO, (self.mcdr_server.server_interface, info))

		if info.is_user:
			self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.USER_INFO, (self.mcdr_server.server_interface, info))


def get_reactor(server):
	return GeneralReactor(server)
