# -*- coding: utf-8 -*-
import time

from utils import info


class BaseParser(object):
	def __init__(self):
		self.STOP_COMMAND = None

	def parse_server_stdout_raw(self, text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = info.Info()
		result.source = info.InfoSource.SERVER
		result.content = result.raw_content = text
		return result

	def parse_server_stdout(self, text):
		return self.parse_server_stdout_raw(text)

	def parse_console_command(self, text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = info.Info()
		result.raw_content = text
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.second = t.tm_sec
		result.content = text
		result.source = info.InfoSource.CONSOLE
		return result

	def parse_player_joined(self, info):
		pass

	def parse_player_left(self, info):
		pass

	def pre_parse_server_stdout(self, text):
		return text

	def is_server_startup_done(self, info):
		return False


parser = BaseParser()
