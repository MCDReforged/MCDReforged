import os

from utils import tool
from utils.parser import bukkit_parser
from utils.parser.vanilla_parser import VanillaParser


class BukkitParser14(VanillaParser):
	# 1.14.4+ bukkit / spigot change it's console logger into vanilla like format
	# idk why they did this
	# paper is not included

	NAME = tool.remove_suffix(os.path.basename(__file__), '.py')

	def __init__(self, parser_manager):
		super().__init__(parser_manager)

	def parse_player_joined(self, info):
		return bukkit_parser.get_parser(self.parser_manager).parse_player_joined(info)


def get_parser(parser_manager):
	return BukkitParser14(parser_manager)

