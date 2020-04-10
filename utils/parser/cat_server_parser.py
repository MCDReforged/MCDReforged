# -*- coding: utf-8 -*-
import copy
import os

from utils import tool
from utils.parser.bukkit_parser import BukkitParser
from utils.parser.vanilla_parser import VanillaParser


class CatServerParser(BukkitParser):
	# https://github.com/Luohuayu/CatServer
	# CatServer uses vanilla logging format but spigot like player joined message
	# And has color code around the player left message

	NAME = os.path.basename(__file__).rstrip('.py')

	def __init__(self, parser_manager):
		super().__init__(parser_manager)

	def parse_server_stdout(self, text):
		return VanillaParser.parse_server_stdout(self, text)

	def parse_player_left(self, info):
		# §eSteve left the game§r
		processed_info = copy.deepcopy(info)
		processed_info.content = tool.clean_minecraft_color_code(processed_info.content)
		return super().parse_player_left(processed_info)


def get_parser(parser_manager):
	return CatServerParser(parser_manager)
