# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


# analyzing and reacting events related to player
class PlayerReactor(BaseReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			# on_player_joined
			player = self.server.parser_manager.get_parser().parse_player_joined(info)
			if player is not None:
				self.server.permission_manager.touch_player(player)
				self.server.plugin_manager.call('on_player_joined', (self.server.server_interface, player))

			# on_player_left
			player = self.server.parser_manager.get_parser().parse_player_left(info)
			if player is not None:
				self.server.plugin_manager.call('on_player_left', (self.server.server_interface, player))

			# on_player_death
			player = self.server.parser_manager.get_parser().parse_player_death(info)
			if player is not None:
				self.server.plugin_manager.call('on_player_death', (self.server.server_interface, player))


def get_reactor(server):
	return PlayerReactor(server)
