# -*- coding: utf-8 -*-
from utils.reactor.base_reactor import BaseReactor


class GeneralReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.content == '!!MCDR reload':
			server.plugin_manager.load_plugins()
		server.plugin_manager.call('on_info', (server.server_interface, info))


reactor = GeneralReactor
