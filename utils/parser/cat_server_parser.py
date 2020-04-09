# -*- coding: utf-8 -*-
import copy
from utils import tool
from utils.parser.bukkit_parser import BukkitParser
from utils.parser.vanilla_parser import VanillaParser


class CatServerParser(BukkitParser):
	# https://github.com/Luohuayu/CatServer
	# CatServer uses vanilla logging format but spigot like player joined message
	# And has color code around the player left message

	def __init__(self):
		VanillaParser.__init__(self)

	def parse_server_stdout(self, text):
		return VanillaParser.parse_server_stdout(self, text)

	def parse_player_left(self, info):
		# §eSteve left the game§r
		processed_info = copy.deepcopy(info)
		processed_info.content = tool.clean_minecraft_color_code(processed_info.content)
		return super().parse_player_left(processed_info)


parser = CatServerParser()
