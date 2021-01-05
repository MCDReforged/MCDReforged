"""
Analyzing and reacting events related to server
"""

from mcdreforged.info import InfoSource
from mcdreforged.plugin.plugin_event import PluginEvents
from mcdreforged.reactor.abstract_reactor import AbstractReactor


class ServerReactor(AbstractReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			parser = self.mcdr_server.parser_manager.get_parser()

			if parser.parse_server_startup_done(info):
				self.mcdr_server.logger.debug('Server startup detected')
				self.mcdr_server.flag_server_startup = True
				self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.SERVER_STARTUP, (self.mcdr_server.server_interface,))

			if parser.parse_rcon_started(info):
				self.mcdr_server.logger.debug('Server rcon started detected')
				self.mcdr_server.flag_server_rcon_ready = True
				self.mcdr_server.connect_rcon()

			if parser.parse_server_stopping(info):
				self.mcdr_server.logger.debug('Server stopping detected')
				self.mcdr_server.rcon_manager.disconnect()


def get_reactor(server):
	return ServerReactor(server)
