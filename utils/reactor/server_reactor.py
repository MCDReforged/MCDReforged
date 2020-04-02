# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


class ServerReactor(BaseReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			player = self.server.parser.parse_player_joined(info)
			if player is not None:
				self.server.permission_manager.touch_player(player)
				self.server.plugin_manager.call('on_player_joined', (self.server.server_interface, player))

			player = self.server.parser.parse_player_left(info)
			if player is not None:
				self.server.plugin_manager.call('on_player_left', (self.server.server_interface, player))

			if self.server.parser.is_server_startup_done(info):
				self.server.connect_rcon()
				self.server.plugin_manager.call('on_server_startup', (self.server.server_interface, ))


def get_reactor(server):
	return ServerReactor(server)
