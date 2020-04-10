# -*- coding: utf-8 -*-
import os
import re
import time

import utils.info
from utils.info import InfoSource


class BaseParser(object):
	NAME = os.path.basename(__file__).rstrip('.py')

	def __init__(self, parser_manager):
		self.STOP_COMMAND = None
		self.parser_manager = parser_manager

	def parse_server_stdout_raw(self, text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = utils.info.Info()
		result.source = InfoSource.SERVER
		result.content = result.raw_content = text
		return result

	def parse_server_stdout(self, text):
		return self.parse_server_stdout_raw(text)

	def parse_console_command(self, text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = utils.info.Info()
		result.raw_content = text
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.second = t.tm_sec
		result.content = text
		result.source = InfoSource.CONSOLE
		return result

	def parse_player_joined(self, info):
		return None

	def parse_player_left(self, info):
		return None

	def parse_player_death(self, info):
		if info.is_user:
			return None
		re_list = self.parser_manager.get_death_message_list(type(self))
		for re_exp in re_list:
			if re.fullmatch(re_exp, info.content):
				return info.content.split(' ')[0]
		return None

	def pre_parse_server_stdout(self, text):
		if text.startswith('\033['):
			text = re.sub(r'\033\[.*?m', '', text)
		return text

	def parse_server_startup_done(self, info):
		return False


def get_parser(parser_manager):
	return BaseParser(parser_manager)
