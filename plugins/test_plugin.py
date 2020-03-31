# -*- coding: utf-8 -*-
import time


loaded_time = time.time()


def on_load(server, old_module):
	if old_module is None:
		server.logger.info('I''m the first one!')
	else:
		server.logger.info('The former one has lived {}s before unload'.format(time.time() - old_module.loaded_time))


def on_unload(server):
	server.logger.info('bye')


def on_info(server, info):
	if info.is_user:
		if info.content == 'ping':
			server.say('pong')
		if info.content == '!!start':
			server.start()
		if info.content == '!!stop':
			server.stop()
		if info.content == '!!restart':
			server.restart()
		if info.content == '!!err':
			x = 1 / 0


def on_player_joined(server, player):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server, player):
	server.say('Bye {}'.format(player))
