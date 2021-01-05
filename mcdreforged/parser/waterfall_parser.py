import os

from mcdreforged import constant
from mcdreforged.parser import bukkit_parser
from mcdreforged.parser.bungeecord_parser import BungeecordParser
from mcdreforged.utils import string_util


class WaterfallParser(BungeecordParser):
	# The logging format of waterfall server is spigot like

	NAME = string_util.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	def parse_server_stdout(self, text):
		return bukkit_parser.get_parser(self.parser_manager).parse_server_stdout(text)


def get_parser(parser_manager):
	return WaterfallParser(parser_manager)
