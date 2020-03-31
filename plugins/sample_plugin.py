# -*- coding: utf-8 -*-


def on_reload(server, old_module):
	pass


def on_info(server, info):
	if info.player is not None and info.content == 'ping':
		server.say('pong')
