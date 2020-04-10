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

			# on_death_message
			if self.server.parser_manager.get_parser().parse_death_message(info):
				self.server.plugin_manager.call('on_death_message', (self.server.server_interface, info.content))

			# on_player_made_advancement
			result = self.server.parser_manager.get_parser().parse_player_made_advancement(info)
			if result is not None:
				player, advancement = result
				self.server.plugin_manager.call('on_player_made_advancement', (self.server.server_interface, player, advancement))


def get_reactor(server):
	return PlayerReactor(server)
