# -*- coding: utf-8 -*-
import os

from utils.parser import bukkit_parser, bungeecord_parser


class WaterfallParser(bungeecord_parser.BungeecordParser):
	# The logging format of waterfall server is spigot like

	NAME = os.path.basename(__file__).rstrip('.py')

	def parse_server_stdout(self, text):
		return bukkit_parser.get_parser(self.parser_manager).parse_server_stdout(text)


def get_parser(parser_manager):
	return WaterfallParser(parser_manager)
