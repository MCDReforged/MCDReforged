# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


class ServerReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.source == InfoSource.SERVER:
			player = server.parser.parse_player_joined(info)
			if player is not None:
				server.permission_manager.touch_player(player)
				server.plugin_manager.call('on_player_joined', (server.server_interface, player))

			player = server.parser.parse_player_left(info)
			if player is not None:
				server.plugin_manager.call('on_player_left', (server.server_interface, player))

			if server.parser.is_server_startup_done(info):
				server.plugin_manager.call('on_server_startup', (server.server_interface, ))


reactor = ServerReactor
