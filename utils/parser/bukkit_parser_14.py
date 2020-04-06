# -*- coding: utf-8 -*-

from utils.parser import vanilla_parser, bukkit_parser


class BukkitParser14(vanilla_parser.VanillaParser):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	def __init__(self):
		super().__init__()
		self.Logger_NAME_CHAR_SET += r'\-'

	def parse_player_joined(self, text):
		return bukkit_parser.parser.parse_player_joined(text)


parser = BukkitParser14()

