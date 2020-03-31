# -*- coding: utf-8 -*-
from utils.info import InfoSource
from utils.reactor.base_reactor import BaseReactor


class GeneralReactor(BaseReactor):
	@staticmethod
	def react(server, info):
		if info.is_user and info.content == '!!MCDR reload':
			msg = server.plugin_manager.load_plugins()
			if info.source == InfoSource.SERVER:
				server.server_interface.say(msg)
		else:
			if info.source == InfoSource.CONSOLE:  # send input command to server's stdin
				server.send(info.content)
			server.plugin_manager.call('on_info', (server.server_interface, info))


reactor = GeneralReactor
