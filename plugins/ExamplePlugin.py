# -*- coding: utf-8 -*-

import random
import re
import time
from utils.rtext import *


PLUGIN_INFO = {
	'id': 'sample-plugin',
	'version': '1.0.0',
	'name': 'Sample Plugin',
	'description': 'Sample plugin for MCDR',
	'author': 'Fallen_Breath',
	'link': 'https://github.com/Fallen-Breath/MCDReforged',
	'depends': {
		'MCDReforged': '>=0.10.0',
	}
}

counter = 0
secret = random.random()


def on_load(server, old_module):
	global counter
	if old_module is not None:
		counter = old_module.counter + 1
	else:
		counter = 1
	msg = f'This is the {counter} time to load the plugin'
	if server.is_server_running():
		server.say(msg)
	server.logger.info(msg)


def on_unload(server):
	server.logger.info('bye')


def on_info(server, info):
	if not info.is_user and re.fullmatch(r'Starting Minecraft server on \S*', info.content):
		server.reply(info, 'The server bound port {}'.format(info.content.split(':')[-1]))


'''
# It works too but not it's not recommend to use
def on_player_joined(server, player):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))
'''


def on_player_joined(server, player, info):
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server, player):
	server.say('Bye {}'.format(player))


def on_death_message(server, message):
	server.say('RIP {}'.format(message.split(' ')[0]))


def on_player_made_advancement(server, player, advancement):
	server.say('Good job {} u have got "{}"'.format(player, advancement))


def on_server_startup(server):
	server.logger.info('Server has started')


def on_server_stop(server, return_code):
	server.logger.info('Server has stopped and its return code is {}'.format(return_code))


def on_mcdr_stop(server):
	# MCDR will wait until all on_mcdr_stop event call is finished before exiting
	server.logger.info('Give me 3 second to prepare exiting')
	for i in range(3):
		time.sleep(1)
	server.logger.info('See you next time~')
