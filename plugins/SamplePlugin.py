import re

from mcdreforged.api.command import *
from mcdreforged.api.types import *

PLUGIN_METADATA = {
	'id': 'sample_plugin',    # contains letter in lowercase, number and underscore
	'version': '1.0.0',       # recommend to follow semver
	'name': 'Sample Plugin',  # RText is allowed
	'description': 'Sample plugin for MCDR',  # RText is allowed
	'author': 'Fallen_Breath',  # A str, or a list of str
	'link': 'https://github.com/Fallen-Breath/MCDReforged',  # A str to your plugin home page
	'dependencies': {
		'mcdreforged': '>=0.10.0',
	}
}

# variant for functionality demo
counter = 0


def on_load(server: ServerInterface, old_module):
	"""
	Do some clean up when your plugin is being loaded
	Like migrating data, reading config file or adding help messages
	old_module is the previous plugin instance. If the plugin is freshly loaded it will be None
	"""
	global counter
	if old_module is not None:
		counter = old_module.counter + 1
	else:
		counter = 1
	msg = f'This is the {counter} time to load the plugin'
	server.logger.info(msg)
	server.add_command(Literal('!!cexample').runs(lambda src: src.reply('Hello world from sample command')))
	server.add_help_message('!!example', 'Hello world')
	server.add_help_message('!!cexample', 'Hello world from command')


def on_unload(server: ServerInterface):
	"""
	Do some clean up when your plugin is being unloaded. Note that it might be a reload
	"""
	server.logger.info('Bye')


def on_removed(server: ServerInterface):
	"""
	Do some clean up when your plugin is being removed from MCDR
	"""
	server.logger.info('Man i got removed')


def on_info(server: ServerInterface, info: Info):
	"""
	Handler for general server output event
	Recommend to use on_user_info instead if you only care about info created by users
	"""
	if not info.is_user and re.fullmatch(r'Starting Minecraft server on \S*', info.content):
		server.logger.info('Minecraft is starting')


def on_user_info(server: ServerInterface, info: Info):
	"""
	Reacting to user input
	"""
	if info.content == '!!example':
		server.reply(info, 'example!!')


def on_player_joined(server: ServerInterface, player: str, info: Info):
	"""
	A new player joined game, welcome!
	"""
	server.tell(player, 'Welcome!')
	server.say('Hi {}'.format(player))


def on_player_left(server: ServerInterface, player: str):
	"""
	A player left the game, do some cleanup!
	"""
	server.say('Bye {}'.format(player))


def on_server_start(server: ServerInterface):
	"""
	When the server begins to start
	"""
	server.logger.info('Server is starting')


def on_server_startup(server: ServerInterface):
	"""
	When the server is fully startup
	"""
	server.logger.info('Server has started')


def on_server_stop(server: ServerInterface, return_code: int):
	"""
	When the server process is stopped, go do some clean up
	If the server is not stopped by a plugin, this is the only chance for plugins to restart the server, otherwise MCDR
	will exit too
	"""
	server.logger.info('Server has stopped and its return code is {}'.format(return_code))


def on_mcdr_start(server: ServerInterface):
	"""
	When MCDR is about to stop, go do some clean up
	MCDR will wait until all on_mcdr_stop event call are finished before exiting
	"""
	server.logger.info('Another new launch for MCDR')


def on_mcdr_stop(server: ServerInterface):
	"""
	When MCDR is about to stop, go do some clean up
	MCDR will wait until all on_mcdr_stop event call are finished before exiting
	"""
	server.logger.info('See you next time~')
