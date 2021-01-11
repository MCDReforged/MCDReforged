"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""

from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.plugin.plugin_event import MCDRPluginEvents


class GeneralReactor(AbstractInfoReactor):
	def react(self, info):
		command_source = info.get_command_source()
		if command_source is not None:
			self.mcdr_server.command_manager.execute_command(command_source, info.content)

		self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.GENERAL_INFO, (info,))

		if info.is_user:
			self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.USER_INFO, (info,))
