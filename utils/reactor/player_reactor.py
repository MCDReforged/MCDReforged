from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


# analyzing and reacting events related to player
class PlayerReactor(BaseReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			parser = self.server.parser_manager.get_parser()

			# on_player_joined
			player = parser.parse_player_joined(info)
			if player is not None:
				self.server.logger.debug('Player joined detected')
				self.server.permission_manager.touch_player(player)
				self.server.plugin_manager.call('on_player_joined', [(self.server.server_interface, player), (self.server.server_interface, player, info)])

			# on_player_left
			player = parser.parse_player_left(info)
			if player is not None:
				self.server.logger.debug('Player left detected')
				self.server.plugin_manager.call('on_player_left', (self.server.server_interface, player))

			# on_death_message
			if parser.parse_death_message(info):
				self.server.logger.debug('Death message detected')
				self.server.plugin_manager.call('on_death_message', (self.server.server_interface, info.content))

			# on_player_made_advancement
			result = parser.parse_player_made_advancement(info)
			if result is not None:
				self.server.logger.debug('Player made advancement detected')
				player, advancement = result
				self.server.plugin_manager.call('on_player_made_advancement', (self.server.server_interface, player, advancement))


def get_reactor(server):
	return PlayerReactor(server)
