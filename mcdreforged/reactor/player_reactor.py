"""
Analyzing and reacting events related to player
"""
from mcdreforged.info import InfoSource
from mcdreforged.plugin.plugin_event import PluginEvents
from mcdreforged.reactor.abstract_inf_reactor import AbstractInfoReactor


class PlayerReactor(AbstractInfoReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			parser = self.mcdr_server.parser_manager.get_parser()

			# on_player_joined
			player = parser.parse_player_joined(info)
			if player is not None:
				self.mcdr_server.logger.debug('Player joined detected')
				self.mcdr_server.permission_manager.touch_player(player)
				self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.PLAYER_JOIN, (self.mcdr_server.server_interface, player, info))

			# on_player_left
			player = parser.parse_player_left(info)
			if player is not None:
				self.mcdr_server.logger.debug('Player left detected')
				self.mcdr_server.plugin_manager.dispatch_event(PluginEvents.PLAYER_LEFT, (self.mcdr_server.server_interface, player))

			# # on_death_message
			# if parser.parse_death_message(info):
			# 	self.mcdr_server.logger.debug('Death message detected')
			# 	self.mcdr_server.plugin_manager.call('on_death_message', (self.mcdr_server.server_interface, info.content))
			#
			# # on_player_made_advancement
			# result = parser.parse_player_made_advancement(info)
			# if result is not None:
			# 	self.mcdr_server.logger.debug('Player made advancement detected')
			# 	player, advancement = result
			# 	self.mcdr_server.plugin_manager.call('on_player_made_advancement', (self.mcdr_server.server_interface, player, advancement))
