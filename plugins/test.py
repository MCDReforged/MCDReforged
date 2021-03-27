from random import random

from mcdreforged.api.all import *

secret = random()


def on_load(server: ServerInterface, prev):
	register_help_message(server)
	server.register_command(Literal('!!mypoint').then(PointArgument('pt').runs(lambda src, ctx: src.reply('You have input a point ({}, {}, {})'.format(*ctx['pt'])))))
	server.register_command(Literal('req1').requires(lambda: False))
	server.register_command(Literal('req2').requires(lambda: False, failure_message_getter=lambda: "as"))


def register_help_message(server):
	server.register_help_message('!!!start', 'Start the server')
	server.register_help_message('!!!stop', 'Stop the server')
	server.register_help_message('!!!stop_exit', 'Stop the server and exit')
	server.register_help_message('!!!restart', 'Restart the server')
	server.register_help_message('!!!exit', 'Exit MCDR when server stopped')
	server.register_help_message('!!!rcon', 'Rcon test')
	server.register_help_message('!!!permission', 'Get permission level')
	server.register_help_message('!!!error', 'What is 1/0?')
	server.register_help_message('!!!status', 'Get server status')
	server.register_help_message('!!!secret', 'get_plugin_instance() test')
	server.register_help_message('!!!rtext', RText('rtext test').h('it', ' ', 'works', RText('?', styles=RStyle.obfuscated)))
	server.register_help_message('!!!plugin', 'plugin test')
	server.register_help_message('!!!color', 'color test')
	server.register_help_message('!!!logger', 'unique logger test')
	server.register_help_message('!!!console', 'special command to console')


def on_user_info(server: ServerInterface, info: Info):
	if info.content == 'ping':
		server.reply(info, 'pong')

	if server.get_permission_level(info) >= PermissionLevel.MCDR_CONTROL_LEVEL:
		if info.content == '!!!start':
			server.start()

		if info.content == '!!!stop':
			server.stop()

		if info.content == '!!!stop_exit':
			server.stop_exit()

		if info.content == '!!!restart':
			server.restart()

		if info.content == '!!!exit':
			try:
				server.exit()
			except IllegalCallError:
				success = False
			else:
				success = True
			server.reply(info, 'success: {}'.format(success))

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
pid: {}
		'''.strip().format(
			server.is_server_running(),
			server.is_server_startup(),
			server.is_rcon_running(),
			server.get_server_pid(),
		))

	if info.content == '!!!secret':
		global secret
		server.reply(
			info, 'My secret number is {}\nAnd You know it too {}'.format(
				secret, server.get_plugin_instance('test').secret
			)
		)

	if info.content == '!!!plugin':
		# getters
		plugin_id = server.get_plugin_list()[0]
		server.reply(info, 'I found "{}"'.format(plugin_id))
		meta = server.get_plugin_metadata(plugin_id)
		server.reply(info, 'I got the metadata of "{}": {}'.format(plugin_id, meta))
		plugin_file_path = server.get_plugin_file_path(plugin_id)
		plugin_file_path_disabled = plugin_file_path + '.disabled'
		server.reply(info, 'I got the file path of "{}": {}'.format(plugin_id, plugin_file_path))

		# manipulations
		server.disable_plugin(plugin_id),					server.reply(info, 'I disabled "{}"'.format(plugin_id))
		server.enable_plugin(plugin_file_path_disabled),	server.reply(info, 'I enabled "{}"'.format(plugin_file_path_disabled))
		server.unload_plugin(plugin_id),					server.reply(info, 'I unloaded "{}"'.format(plugin_id))
		server.load_plugin(plugin_file_path),				server.reply(info, 'I loaded "{}"'.format(plugin_file_path))
		server.reload_plugin(plugin_id),					server.reply(info, 'I reloaded "{}"'.format(plugin_id))
		server.refresh_changed_plugins(),					server.reply(info, 'I refreshed all changed plugins')
		server.refresh_all_plugins(),						server.reply(info, 'I refreshed EVERYTHING!')

	if info.content == '!!!rtext':
		server.reply(info, RText('RText!!', color=RColor.gold))
		server.reply(
			info,
			RText('hover! ', color=RColor.aqua).set_hover_text('~~~') +
			RText('click!', styles=RStyle.underlined).set_click_event(RAction.suggest_command, 'yes!')
		)
		server.reply(
			info,
			RText('More Test', color=RColor.light_purple, styles=[RStyle.italic, RStyle.underlined]).h('QwQ') +
			'\nMinecraft §aC§bo§cl§do§er §r§lCode\n' +
			RTextList(
				RText('>>>>>>> Click me <<<<<<<\n').c(RAction.suggest_command, '!!!rtext').h(
					RText('www', styles=[RStyle.obfuscated, RStyle.underlined]),
					'<- guess what is this\n',
					'tbh idk'
				),
				RText('Have you clicked§f that?', styles=RStyle.bold).h('stop lazy')
			)
		)

	if info.content == '!!!color':
		if info.is_player:
			text = RTextList()
			text.append(*[RText(color.name + '\n', color=color) for color in RColor])
			text.append(*[RText(style.name + '\n', styles=style) for style in RStyle])
		else:
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

	if info.content == '!!!logger':
		server.logger.info('awa')

	if info.content == '!!!console':
		server.reply(info, 'This is the reply to player', console_text='This is the reply to console')


class IllegalPoint(CommandSyntaxError):
	def __init__(self, char_read: int):
		super().__init__('Invalid Point', char_read)


class IncompletePoint(CommandSyntaxError):
	def __init__(self, char_read: int):
		super().__init__('Incomplete Point', char_read)


class PointArgument(ArgumentNode):
	def parse(self, text: str) -> ParseResult:
		total_read = 0
		coords = []
		for i in range(3):
			value, read = command_builder_util.get_float(text[total_read:])
			if read == 0:
				raise IncompletePoint(total_read)
			total_read += read
			if value is None:
				raise IllegalPoint(total_read)
			coords.append(value)
		return ParseResult(coords, total_read)
