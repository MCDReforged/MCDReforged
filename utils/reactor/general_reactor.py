# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


class GeneralReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.content == '!!MCDR reload':
			server.plugin_manager.load_plugins()
		else:
			if info.source == InfoSource.CONSOLE:
				server.send(info.content)
			server.plugin_manager.call('on_info', (server.server_interface, info))


reactor = GeneralReactor
