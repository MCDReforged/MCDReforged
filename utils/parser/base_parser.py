# -*- coding: utf-8 -*-
import time

from utils import info


class BaseParser(object):
	@staticmethod
	def parse_server_stdout(text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = info.Info()
		result.source = info.InfoSource.SERVER
		return result

	@staticmethod
	def parse_console_command(text):
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = info.Info()
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.second = t.tm_sec
		result.content = text
		result.source = info.InfoSource.CONSOLE
		return result


parser = BaseParser
