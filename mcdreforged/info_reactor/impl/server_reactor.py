"""
Analyzing and reacting events related to server
"""

from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.info_reactor.info import InfoSource
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.mcdr_state import MCDReforgedFlag
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.utils.logger import DebugOption


class ServerReactor(AbstractInfoReactor):
	@property
	def server_info(self) -> ServerInformation:
		return self.mcdr_server.server_information

	def on_server_start(self):
		self.server_info.clear()

	def react(self, info):
		if info.source == InfoSource.SERVER:
			handler = self.mcdr_server.server_handler_manager.get_current_handler()

			if handler.test_server_startup_done(info):
				self.mcdr_server.logger.debug('Server startup detected', option=DebugOption.REACTOR)
				self.mcdr_server.with_flag(MCDReforgedFlag.SERVER_STARTUP)
				self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.SERVER_STARTUP, ())

			version = handler.parse_server_version(info)
			if version is not None:
				self.mcdr_server.logger.debug('Server version detected: {}'.format(version), option=DebugOption.REACTOR)
				self.server_info.version = version

			ip_and_port = handler.parse_server_address(info)
			if ip_and_port is not None:
				self.mcdr_server.logger.debug('Server ip detected: {}:{}'.format(*ip_and_port), option=DebugOption.REACTOR)
				self.server_info.ip, self.server_info.port = ip_and_port

			if handler.test_rcon_started(info):
				self.mcdr_server.logger.debug('Server rcon started detected', option=DebugOption.REACTOR)
				self.mcdr_server.with_flag(MCDReforgedFlag.SERVER_RCON_READY)
				self.mcdr_server.connect_rcon()

			if handler.test_server_stopping(info):  # notes that it might happen more than once in the server lifecycle
				self.mcdr_server.logger.debug('Server stopping detected', option=DebugOption.REACTOR)
				self.mcdr_server.rcon_manager.disconnect()
