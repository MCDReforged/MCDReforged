# -*- coding: utf-8 -*-


counter = 0


def on_load(server, old_module):
	global counter
	if old_module is not None:
		counter = old_module.counter + 1
	else:
		counter = 1
	msg = f'This is the {counter} time to load the plugin'
	if server.is_running():
		server.say(msg)
	server.logger.info(msg)


def on_unload(server):
	server.logger.info('bye')


def on_info(server, info):
	if info.is_user:
		if info.content == 'ping':
			server.say('pong')
		if server.get_permission_level(info) == 3:
			if info.content == '!!start':
				server.start()
			if info.content == '!!stop':
				server.stop_exit()
			if info.content == '!!restart':
				server.restart()
		if info.source == 1 and info.content.startswith('say '):
			server.say(info.content[4:])
		if info.is_player:
			if info.content == '!!permission':
				server.tell(info.player, server.get_permission_level(info))


def on_player_joined(server, player):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server, player):
	server.say('Bye {}'.format(player))


def on_server_startup(server):
	server.logger.info('Server has started')


def on_mcdr_stop(server):
	server.logger.info('See you next time~')
