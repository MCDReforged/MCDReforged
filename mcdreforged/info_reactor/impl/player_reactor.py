"""
Analyzing and reacting events related to player
"""
from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.info_reactor.info import InfoSource
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.utils.logger import DebugOption


class PlayerReactor(AbstractInfoReactor):
	def react(self, info):
		if info.source == InfoSource.SERVER:
			handler = self.mcdr_server.server_handler_manager.get_current_handler()

			# on_player_joined
			player = handler.parse_player_joined(info)
			if player is not None:
				self.mcdr_server.logger.debug('Player joined detected', option=DebugOption.REACTOR)
				self.mcdr_server.permission_manager.touch_player(player)
				self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.PLAYER_JOINED, (player, info))

			# on_player_left
			player = handler.parse_player_left(info)
			if player is not None:
				self.mcdr_server.logger.debug('Player left detected', option=DebugOption.REACTOR)
				self.mcdr_server.plugin_manager.dispatch_event(MCDRPluginEvents.PLAYER_LEFT, (player,))

			# # on_death_message
			# if handler.parse_death_message(info):
			# 	self.mcdr_server.logger.debug('Death message detected')
			# 	self.mcdr_server.plugin_manager.call('on_death_message', (self.mcdr_server.server_interface, info.content))
			#
			# # on_player_made_advancement
			# result = handler.parse_player_made_advancement(info)
			# if result is not None:
			# 	self.mcdr_server.logger.debug('Player made advancement detected')
			# 	player, advancement = result
			# 	self.mcdr_server.plugin_manager.call('on_player_made_advancement', (self.mcdr_server.server_interface, player, advancement))
