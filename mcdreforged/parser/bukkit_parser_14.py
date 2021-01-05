import os

from mcdreforged import constant
from mcdreforged.parser import bukkit_parser
from mcdreforged.parser.vanilla_parser import VanillaParser
from mcdreforged.utils import string_util


class BukkitParser14(VanillaParser):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	NAME = string_util.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	def __init__(self, parser_manager):
		super().__init__(parser_manager)

	def parse_player_joined(self, info):
		return bukkit_parser.get_parser(self.parser_manager).parse_player_joined(info)


def get_parser(parser_manager):
	return BukkitParser14(parser_manager)

