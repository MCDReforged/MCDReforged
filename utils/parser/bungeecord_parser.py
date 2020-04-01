# -*- coding: utf-8 -*-

import re
from utils.parser import base_parser


class BungeecordParser(base_parser.BaseParser):
	STOP_COMMAND = 'end'

	@staticmethod
	def parse_server_stdout(text):
		raw_result = result = super(BungeecordParser, BungeecordParser).parse_server_stdout(text)
		try:

			# 09:00:02 [信息] Listening on /0.0.0.0:25565
			# 09:00:01 [信息] [Steve] -> UpstreamBridge has disconnected
			time_data = re.search(r'[0-9]*:[0-9]*:[0-9]* ', text).group()
			elements = time_data[0:-1].split(':')
			result.hour = int(elements[0])
			result.min = int(elements[1])
			result.sec = int(elements[2])

			text = text.replace(time_data, '', 1)
			# [信息] Listening on /0.0.0.0:25565
			# [信息] [Steve] -> UpstreamBridge has disconnected

			text = text.replace(re.match(r'\[.*\] ', text).group(), '', 1)
			# Listening on /0.0.0.0:25565
			# [Steve] -> UpstreamBridge has disconnected

			result.content = text
			return result
		except:
			return raw_result

	@staticmethod
	def pre_parse_server_stdout(text):
		match = re.match(r'>*\r', text)
		if match is not None:
			text = text.replace(match.group(), '', 1)
		return text

	@staticmethod
	def is_server_startup_done(info):
		# Listening on /0.0.0.0:25577
		if info.is_user:
			return False
		match = re.fullmatch(r'Listening on /[0-9.]+:[0-9]+', info.content)
		return match is not None


parser = BungeecordParser
