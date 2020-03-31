# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


class ServerReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.source == InfoSource.SERVER:
			if info.content.endswith('joined the game'):
				player = info.content.split(' ')[0]
				server.plugin_manager.call('on_player_joined', (server.server_interface, player))
			if info.content.endswith('left the game'):
				player = info.content.split(' ')[0]
				server.plugin_manager.call('on_player_left', (server.server_interface, player))


reactor = ServerReactor
