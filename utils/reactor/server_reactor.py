# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


# analyzing and reacting events related to server
class ServerReactor(BaseReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			if self.server.parser_manager.get_parser().parse_server_startup_done(info):
				self.server.flag_server_startup = True
				self.server.connect_rcon()
				self.server.plugin_manager.call('on_server_startup', (self.server.server_interface, ))


def get_reactor(server):
	return ServerReactor(server)
