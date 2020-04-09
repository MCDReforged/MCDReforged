# -*- coding: utf-8 -*-

from utils.parser import bukkit_parser, bungeecord_parser


class WaterfallParser(bungeecord_parser.BungeecordParser):
	# The logging format of waterfall server is spigot like

	def parse_server_stdout(self, text):
		return bukkit_parser.parser.parse_server_stdout(text)


parser = WaterfallParser()
