"""
The basic plain parser
"""


import os

from mcdr import tool, constant
from mcdr.info import Info
from mcdr.parser.abstract_parser import AbstractParser


class BasicParser(AbstractParser):
	NAME = tool.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	def parse_server_stdout(self, text):
		return self._parse_server_stdout_raw(text)

	def parse_player_joined(self, info):
		return None

	def parse_player_left(self, info):
		return None

	def parse_player_made_advancement(self, info):
		return None

	def parse_server_startup_done(self, info):
		return False

	def parse_rcon_started(self, info: Info):
		return False

	def parse_server_stopping(self, info: Info):
		return False


def get_parser(parser_manager):
	return BasicParser(parser_manager)
