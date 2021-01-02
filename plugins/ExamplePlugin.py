# -*- coding: utf-8 -*-

import random
import re
import time


PLUGIN_METADATA = {
	'id': 'sample-plugin',
	'version': '1.0.0',
	'name': 'Sample Plugin',
	'description': 'Sample plugin for MCDR',
	'author': 'Fallen_Breath',
	'link': 'https://github.com/Fallen-Breath/MCDReforged',
	'dependencies': {
		'MCDReforged': '>=0.10.0',
	}
}

# variant for functionality demo
counter = 0
secret = random.random()


def on_load(server, old_module):
	"""
	Do some clean up when your plugin is being loaded
	Like migrating data, reading config file or adding help messages

	:param old_module: Previous plugin instance. If the plugin is freshly loaded it will be None
	:param server: A ServerInterface instance
	"""
	global counter
	if old_module is not None:
		counter = old_module.counter + 1
	else:
		counter = 1
	msg = f'This is the {counter} time to load the plugin'
	server.logger.info(msg)
	server.add_help_message('!!example', 'Hello world')


def on_unload(server):
	"""
	Do some clean up when your plugin is being unloaded

	:param server: A ServerInterface instance
	"""
	server.logger.info('bye')


def on_info(server, info):
	"""
	Handler for general server output event
	Recommend to use on_user_info instead if you only care about info created by users

	:param server: A ServerInterface instance
	:param info: a Info instance
	"""
	if not info.is_user and re.fullmatch(r'Starting Minecraft server on \S*', info.content):
		server.reply(info, 'The server bound port {}'.format(info.content.split(':')[-1]))


def on_user_info(server, info):
	"""
	Reacting to user input

	:param server: A ServerInterface instance
	:param info: a Info instance
	"""
	if info.content == '!!example':
		server.reply(info, 'Hello world!')


'''
# It works too but not it's not recommend to use
def on_player_joined(server, player):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))
'''


def on_player_joined(server, player, info):
	"""
	A new player joined game, welcome!

	:param server: A ServerInterface instance
	:param str player: The name of the player
	:param info: a Info instance, go parse it if you want more information
	"""
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server, player):
	"""
	A player left the game, do some cleanup!

	:param server: A ServerInterface instance
	:param str player: The name of the player
	"""
	server.say('Bye {}'.format(player))


def on_death_message(server, message):
	"""
	RIP someone

	:param server: A ServerInterface instance
	:param str message: The death message
	"""
	server.say('RIP {}'.format(message.split(' ')[0]))


def on_player_made_advancement(server, player, advancement):
	"""
	Someone just made an advancement, congratulations!

	:param server: A ServerInterface instance
	:param str player: The name of the player
	:param str advancement: The name of the advancement / challenge / goal
	"""
	server.say('Good job {} u have got "{}"'.format(player, advancement))


def on_server_startup(server):
	"""
	When the server is fully startup

	:param server: A ServerInterface instance
	"""
	server.logger.info('Server has started')


def on_server_stop(server, return_code):
	"""
	When the server process is stopped, go do some clean up
	If the server is not stopped by a plugin, this is the only chance for plugins to restart the server, otherwise MCDR
	will exit too
	MCDR will wait until all on_server_stop event call are finished before exiting

	:param int return_code: The return code of the process
	:param server: A ServerInterface instance
	"""
	server.logger.info('Server has stopped and its return code is {}'.format(return_code))


def on_mcdr_stop(server):
	"""
	When MCDR is about to stop, go do some clean up
	MCDR will wait until all on_mcdr_stop event call are finished before exiting

	:param server: A ServerInterface instance
	"""
	server.logger.info('Give me 3 second to prepare exiting')
	time.sleep(3)
	server.logger.info('See you next time~')
