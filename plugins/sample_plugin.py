# -*- coding: utf-8 -*-


counter = 0


def on_load(server, old_module):
	global counter
	if old_module is not None:
		counter = old_module.counter + 1
	else:
		counter = 1
	server.say(f'This is the {counter} time to load the plugin')


def on_unload(server):
	server.logger.info('bye')


def on_info(server, info):
	if info.is_user:
		if info.content == 'ping':
			server.say('pong')
		if info.content == '!!start':
			server.start()
		if info.content == '!!stop':
			server.stop_exit()
		if info.content == '!!restart':
			server.restart()
		if info.source == 1 and info.content.startswith('say '):
			server.say(info.content[4:])


def on_player_joined(server, player):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server, player):
	server.say('Bye {}'.format(player))
