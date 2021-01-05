import os
import re

from mcdreforged import constant
from mcdreforged.info import Info
from mcdreforged.parser.abstract_parser import AbstractParser
from mcdreforged.utils import string_util


class BungeecordParser(AbstractParser):
	NAME = string_util.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)
	STOP_COMMAND = 'end'

	def __init__(self, parser_manager):
		super().__init__(parser_manager)

	def parse_server_stdout(self, text):
		result = self._parse_server_stdout_raw(text)

		# 09:00:02 [信息] Listening on /0.0.0.0:25565
		# 09:00:01 [信息] [Steve] -> UpstreamBridge has disconnected
		time_data = re.search(r'[0-9]*:[0-9]*:[0-9]* ', text).group()
		elements = time_data[0:-1].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.sec = int(elements[2])

		text = text.replace(time_data, '', 1)
		result.logging_level = text.split(' ')[0][1:-1]
		# [信息] Listening on /0.0.0.0:25565
		# [信息] [Steve] -> UpstreamBridge has disconnected

		text = text.replace(re.match(r'\[\w+?\] ', text).group(), '', 1)
		# Listening on /0.0.0.0:25565
		# [Steve] -> UpstreamBridge has disconnected

		result.content = text
		return result

	def pre_parse_server_stdout(self, text):
		text = super().pre_parse_server_stdout(text)
		match = re.match(r'>*\r', text)
		if match is not None:
			text = text.replace(match.group(), '', 1)
		return text

	def parse_player_joined(self, info):
		# [Steve,/127.0.0.1:3631] <-> InitialHandler has connected
		if not info.is_user and re.fullmatch(r'\[\w{1,16},/[0-9.]+:[0-9]+\] <-> InitialHandler has connected', info.content):
			return info.content[1:].split(',/')[0]
		return None

	def parse_player_left(self, info):
		# [Steve] -> UpstreamBridge has disconnected
		if not info.is_user and re.fullmatch(r'\[\w{1,16}\] -> UpstreamBridge has disconnected', info.content):
			return info.content[1:].split('] -> ')[0]
		return None

	def parse_server_startup_done(self, info):
		# Listening on /0.0.0.0:25577
		return not info.is_user and re.fullmatch(r'Listening on /[0-9.]+:[0-9]+', info.content) is not None

	def parse_rcon_started(self, info):
		return self.parse_server_startup_done(info)

	def parse_server_stopping(self, info) -> bool:
		# Closing listener [id: 0x3acae0b0, L:/0:0:0:0:0:0:0:0:25565]
		return not info.is_user and re.fullmatch(r'Closing listener \[id: .+, L:[\d:/]+\]', info.content) is not None

	def parse_death_message(self, info: Info) -> bool:
		return False

	def parse_player_made_advancement(self, info: Info):
		return None


def get_parser(parser_manager):
	return BungeecordParser(parser_manager)
