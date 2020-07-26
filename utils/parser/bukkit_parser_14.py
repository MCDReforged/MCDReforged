# -*- coding: utf-8 -*-
import os

from utils import tool
from utils.parser import vanilla_parser, bukkit_parser


class BukkitParser14(vanilla_parser.VanillaParser):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	NAME = tool.remove_suffix(os.path.basename(__file__), '.py')

	def __init__(self, parser_manager):
		super().__init__(parser_manager)


def get_parser(parser_manager):
	return BukkitParser14(parser_manager)

