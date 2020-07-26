# -*- coding: utf-8 -*-
import os
import re
import time

from utils import tool
from utils.info import InfoSource, Info


class BaseParser(object):
	NAME = tool.remove_suffix(os.path.basename(__file__), '.py')
	STOP_COMMAND = ''

	def __init__(self, parser_manager):
		self.parser_manager = parser_manager

	# base parsing, return a Info instance
	def parse_server_stdout_raw(self, text: str) -> Info:
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info()
		result.source = InfoSource.SERVER
		result.content = result.raw_content = text
		return result

	def parse_server_stdout(self, text: str) -> Info:
		return self.parse_server_stdout_raw(text)

	# base parsing, return a Info instance
	def parse_console_command(self, text: str) -> Info:
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info()
		result.raw_content = text
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.sec = t.tm_sec
		result.content = text
		result.source = InfoSource.CONSOLE
		return result

	# returns a str indicating the name of the player
	# if not matches return None
	def parse_player_joined(self, info: Info):
		return None

	# returns 1 str: player_name
	# if not matches return None
	def parse_player_left(self, info: Info):
		return None

	# returns 1 bool: if info.content is a death message
	def parse_death_message(self, info: Info) -> bool:
		if info.is_user:
			return False
		re_list = self.parser_manager.get_death_message_list(type(self))
		for re_exp in re_list:
			if re.fullmatch(re_exp, info.content):
				return True
		return False

	# returns 2 str: player_name, advancement_name
	# if not matches return None
	def parse_player_made_advancement(self, info: Info):
		return None

	def pre_parse_server_stdout(self, text: str) -> str:
		return tool.clean_console_color_code(text)

	# returns 1 bool: if info is a server startup message
	def parse_server_startup_done(self, info: Info) -> bool:
		return False

	def parse_rcon_started(self, info: Info) -> bool:
		return False

	def parse_server_stopping(self, info: Info) -> bool:
		return False


def get_parser(parser_manager):
	return BaseParser(parser_manager)
