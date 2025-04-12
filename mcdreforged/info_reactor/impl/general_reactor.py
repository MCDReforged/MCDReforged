"""
For reacting general info
Including on_info and !!MCDR, !!help command
"""
from typing_extensions import override

from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.info_reactor.info import Info
from mcdreforged.plugin.plugin_event import MCDRPluginEvents


class GeneralReactor(AbstractInfoReactor):
	@override
	def react(self, info: Info):
		command_source = info.get_command_source()
		if command_source is not None:
			self.mcdr_server.command_manager.execute_command(info.content, command_source)

		# The subsequent code flow needs to check the `cancel_send_to_server` status of the `info`,
		# so the `dispatch_event` calls here needs cannot be delay with `DispatchEventPolicy.always_new_task`
		dp_ensure_on_thread = self.mcdr_server.plugin_manager.DispatchEventPolicy.ensure_on_thread
		self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.GENERAL_INFO, (info,), dispatch_policy=dp_ensure_on_thread)

		if info.is_user:
			self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.USER_INFO, (info,), dispatch_policy=dp_ensure_on_thread)
