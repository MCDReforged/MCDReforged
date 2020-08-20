import os

from utils import tool, constant
from utils.parser import bukkit_parser
from utils.parser.bungeecord_parser import BungeecordParser


class WaterfallParser(BungeecordParser):
	# The logging format of waterfall server is spigot like

	NAME = tool.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	def parse_server_stdout(self, text):
		return bukkit_parser.get_parser(self.parser_manager).parse_server_stdout(text)


def get_parser(parser_manager):
	return WaterfallParser(parser_manager)
