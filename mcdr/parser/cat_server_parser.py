import copy
import os

from mcdr import constant
from mcdr.parser.bukkit_parser import BukkitParser
from mcdr.parser.vanilla_parser import VanillaParser
from mcdr.utils import string_util


class CatServerParser(BukkitParser):
	# https://github.com/Luohuayu/CatServer
	# CatServer uses vanilla logging format but spigot like player joined message
	# And has color code around the player left message

	NAME = string_util.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	def parse_server_stdout(self, text):
		return VanillaParser.parse_server_stdout(self, text)

	def parse_player_left(self, info):
		# §eSteve left the game§r
		return super().parse_player_left(cleaned_info(info))

	def parse_player_made_advancement(self, info):
		# § before advancement name
		return super().parse_player_made_advancement(cleaned_info(info))


def get_parser(parser_manager):
	return CatServerParser(parser_manager)


def cleaned_info(info):
	processed_info = copy.deepcopy(info)
	processed_info.content = string_util.clean_minecraft_color_code(processed_info.content)
	return processed_info
