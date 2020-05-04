# -*- coding: utf-8 -*-

import random
from utils.rtext import *

counter = 0
secret = random.random()


def add_help_message(server):
	server.add_help_message('!!!start', 'Start the server')
	server.add_help_message('!!!stop', 'Stop the server')
	server.add_help_message('!!!restart', 'Restart the server')
	server.add_help_message('!!!rcon', 'Rcaon test')
	server.add_help_message('!!!permission', 'Get permission level')
	server.add_help_message('!!!error', 'What is 1/0?')
	server.add_help_message('!!!status', 'Get server status')
	server.add_help_message('!!!secret', 'get_plugin_instance() test')
	server.add_help_message('!!!rtext', RText('rtext test').set_hover_text('it', ' ', 'works', RText('?', styles=RStyle.obfuscated)))
	server.add_help_message('!!!plugin', RText('rtext test').set_hover_text('it', ' ', 'works', RText('?', styles=RStyle.obfuscated)))


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
	add_help_message(server)


def on_unload(server):
	server.logger.info('bye')


def on_info(server, info):
	if info.is_user:
		if info.content == 'ping':
			server.reply(info, 'pong')
		if server.get_permission_level(info) == 3:
			if info.content == '!!!start':
				server.start()
			if info.content == '!!!stop':
				server.stop_exit()
			if info.content == '!!!restart':
				server.restart()
		if info.source == 1 and info.content.startswith('!!!say '):
			server.say(info.content[6:])
		if info.content == '!!!rcon':
			server.reply(info, 'rcon is running? ' + str(server.is_rcon_running()))
			if server.is_rcon_running():
				server.reply(info, '"time query gametime" command result: ' + server.rcon_query('time query gametime'))
		if info.content == '!!!permission':
			server.reply(info, 'Your permission level is {}'.format(server.get_permission_level(info)))
		if info.content == '!!!error':
			x = 1 / 0
		if info.content == '!!!status':
			server.reply(info, '''
is_server_running: {}
is_server_startup: {}
is_rcon_running: {}
			'''.strip().format(
				server.is_server_running(),
				server.is_server_startup(),
				server.is_rcon_running(),
			))
		if info.content == '!!!secret':
			global secret
			server.reply(info, 'My secret number is {}\nAnd You know it too {}'.format(
				secret, server.get_plugin_instance('sample_plugin').secret)
			)
		if info.content == '!!!plugin':
			name = server.get_plugin_list()[0]
			server.reply(info, 'I found "{}"'.format(name))
			server.disable_plugin(name)
			server.reply(info, 'I disabled "{}"'.format(name))
			server.enable_plugin(name)
			server.reply(info, 'I enabled "{}"'.format(name))
			server.load_plugin(name)
			server.reply(info, 'I reloaded "{}"'.format(name))
			server.refresh_changed_plugins()
			server.reply(info, 'I refreshed all changed plugins')
			server.refresh_all_plugins()
			server.reply(info, 'I refreshed EVERYTHING!')
		if info.content == '!!!rtext':
			server.reply(info,
				RText('RText Test', color=RColor.light_purple, styles=RStyle.italic).set_hover_text('QwQ') +
				'\n===\n' +
				RTextList(
					RText('>>>>>>> Click me <<<<<<<\n').set_click_event(RAction.suggest_command, '!!!RText').set_hover_text(
						RText('www', styles=[RStyle.obfuscated, RStyle.underlined]),
						'<- guess what is this\n',
						'tbh idk'
					),
					RText('Have you clicked§f that?', styles=RStyle.bold).set_hover_text('stop lazy')
				)
			)
		if info.content == '!!!color':
			text = '''
			§0black
			§1dark_blue
			§2dark_green
			§3dark_aqua
			§4dark_red
			§5dark_purple
			§6gold
			§7gray
			§8dark_gray
			§9blue
			§agreen
			§baqua
			§cred
			§dlight_purple
			§eyellow
			§fwhite
			§lbold
			§r§krandom (won't work)
			'''.strip()
			text = '\n'.join([line.strip() for line in text.splitlines()])
			server.reply(info, text)
			server.logger.warning(text)


def on_player_joined(server, player):
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
	server.logger.info('See you next time~')
