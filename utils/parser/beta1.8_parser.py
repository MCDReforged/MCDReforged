import os
import re

from utils import tool
from utils.info import Info
from utils.parser.vanilla_parser import VanillaParser


class Beta18Parser(VanillaParser):
	NAME = tool.remove_suffix(os.path.basename(__file__), '.py')
	PLAYER_JOINED_PATTERN = re.compile(r'\w{1,16} \[(?:/[\d.:]+|local)\] logged in with entity id \d+ at \([\dE\-., ]+\)')
	PLAYER_LEFT_PATTERN = re.compile(r'\w{1,16} lost connection: \w+')

	def parse_server_stdout(self, text):
		result = self._parse_server_stdout_raw(text)
		# 2020-12-27 02:56:35 [INFO] Loading properties
		# 2020-12-27 02:57:42 [INFO] <Steve> ping
		time_data = re.search(r' [0-9]*:[0-9]*:[0-9]* ', text).group()
		elements = time_data[1:-1].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.sec = int(elements[2])

		text = text.split(' ', 2)[2]
		# [INFO] Loading properties
		# [INFO] <Steve> ping
		logging, text = text.split(' ', 1)
		result.logging_level = logging[1:-1]
		# Loading properties
		# <Steve> ping

		result.player = re.match(r'^<\w+> ', text)
		if result.player is None:
			result.content = text
		else:
			result.player = result.player.group()[1:-2]
			result.content = text.replace(f'<{result.player}> ', '', 1)
		return result

	def parse_player_joined(self, info):
		# Steve [/127.0.0.1:2993] logged in with entity id 3827 at (-130.5, 69.0, 253.5)
		if not info.is_user and self.PLAYER_JOINED_PATTERN.fullmatch(info.content):
			return info.content.split(' [', 1)[0]

	def parse_player_left(self, info):
		# Steve lost connection: disconnect.quitting
		if not info.is_user and self.PLAYER_LEFT_PATTERN.fullmatch(info.content):
			return info.content.split(' ')[0]

	def parse_player_made_advancement(self, info):
		return None

	def parse_server_startup_done(self, info):
		# Done (6368115300ns)! For help, type "help" or "?"
		if info.is_user:
			return False
		match = re.fullmatch(r'Done \([0-9.]*ns\)! For help, type "help" or "\?"', info.content)
		return match is not None

	def parse_rcon_started(self, info: Info):
		return False

	def parse_server_stopping(self, info: Info):
		# Stopping server
		return not info.is_user and info.content == 'Stopping server'


def get_parser(parser_manager):
	return Beta18Parser(parser_manager)
