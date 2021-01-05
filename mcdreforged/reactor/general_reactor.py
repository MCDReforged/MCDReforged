"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""

from mcdreforged.plugin.plugin_event import PluginEvents
from mcdreforged.reactor.abstract_inf_reactor import AbstractInfoReactor


class GeneralReactor(AbstractInfoReactor):
	def react(self, info):
		if info.is_user:
			self.mcdr_server.command_manager.execute_command(info.to_command_source(), info.content)

		self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.GENERAL_INFO, (self.mcdr_server.server_interface, info))

		if info.is_user:
			self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.USER_INFO, (self.mcdr_server.server_interface, info))
