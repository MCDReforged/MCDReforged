"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""

from mcdreforged.plugin.plugin_event import PluginEvents
from mcdreforged.reactor.abstract_info_reactor import AbstractInfoReactor


class GeneralReactor(AbstractInfoReactor):
	def react(self, info):
		command_source = info.get_command_source()
		if command_source is not None:
			self.mcdr_server.command_manager.execute_command(command_source, info.content)

		self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.GENERAL_INFO, (info, ))

		if info.is_user:
			self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.USER_INFO, (info, ))
