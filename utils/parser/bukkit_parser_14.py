# -*- coding: utf-8 -*-
import os

from utils.parser import vanilla_parser, bukkit_parser


class BukkitParser14(vanilla_parser.VanillaParser):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	NAME = os.path.basename(__file__).rstrip('.py')

	def __init__(self, parser_manager):
		super().__init__(parser_manager)
		self.Logger_NAME_CHAR_SET += r'\-'

	def parse_player_joined(self, text):
		return bukkit_parser.get_parser(self.parser_manager).parse_player_joined(text)


def get_parser(parser_manager):
	return BukkitParser14(parser_manager)

