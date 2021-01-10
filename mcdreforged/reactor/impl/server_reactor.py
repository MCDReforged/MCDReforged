"""
Analyzing and reacting events related to server
"""

from mcdreforged.info import InfoSource
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.utils.logger import DebugOption


class ServerReactor(AbstractInfoReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			handler = self.mcdr_server.server_handler_manager.get_current_handler()

			if handler.test_server_startup_done(info):
				self.mcdr_server.logger.debug('Server startup detected', option=DebugOption.REACTOR)
				self.mcdr_server.flag_server_startup = True
				self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_STARTUP, ())

			if handler.test_rcon_started(info):
				self.mcdr_server.logger.debug('Server rcon started detected', option=DebugOption.REACTOR)
				self.mcdr_server.flag_server_rcon_ready = True
				self.mcdr_server.connect_rcon()

			if handler.test_server_stopping(info):
				self.mcdr_server.logger.debug('Server stopping detected', option=DebugOption.REACTOR)
				self.mcdr_server.rcon_manager.disconnect()
