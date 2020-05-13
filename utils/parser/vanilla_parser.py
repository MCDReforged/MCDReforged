# -*- coding: utf-8 -*-
import os
import re
from utils.parser import base_parser


class VanillaParser(base_parser.BaseParser):
	NAME = os.path.basename(__file__).rstrip('.py')

	def __init__(self, parser_manager):
		super().__init__(parser_manager)
		self.STOP_COMMAND = 'stop'
		self.Logger_NAME_CHAR_SET = r'\w /\#\-'

	def parse_server_stdout(self, text):
		result = self.parse_server_stdout_raw(text)

		# [09:00:00] [Server thread/INFO]: <Steve> Hello
		# [09:00:01] [Server thread/WARN]: Can't keep up!
		time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9]*\] ', text).group()
		elements = time_data[1:-2].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.sec = int(elements[2])

		text = text.replace(time_data, '', 1)
		# [Server thread/INFO]: <Steve> Hello
		# [Server thread/WARN]: Can't keep up!

		logging = re.match(r'^\[[{}]*?\]: '.format(self.Logger_NAME_CHAR_SET), text).group()
		result.logging_level = re.search(r'(?<=/)\w+(?=\]: )', logging).group()
		text = text.replace(logging, '', 1)
		# <Steve> Hello
		# Can't keep up!

		result.player = re.match(r'<\w+> ', text)
		if result.player is None:
			result.content = text
		else:
			result.player = result.player.group()[1:-2]
			result.content = text.replace(f'<{result.player}> ', '', 1)
		return result

	def parse_player_joined(self, info):
		# Steve joined the game
		if not info.is_user and re.fullmatch(r'\w{1,16} joined the game', info.content):
			return info.content.split(' ')[0]
		return None

	def parse_player_left(self, info):
		# Steve left the game
		if not info.is_user and re.fullmatch(r'\w{1,16} left the game', info.content):
			return info.content.split(' ')[0]
		return None

	def parse_player_made_advancement(self, info):
		# Steve has made the advancement [Stone Age]
		if info.is_user:
			return None
		match = re.fullmatch(r'\w{1,16} has made the advancement \[.+\]', info.content)
		if match is not None:
			player, rest = info.content.split(' ', 1)
			adv = re.search(r'(?<=has made the advancement \[).+(?=\])', rest).group()
			return player, adv
		return None

	def parse_server_startup_done(self, info):
		# 1.13+ Done (3.500s)! For help, type "help"
		# 1.13- Done (3.500s)! For help, type "help" or "?"
		if info.is_user:
			return False
		match = re.fullmatch(r'Done \([0-9.]*s\)! For help, type "help"( or "\?")?', info.content)
		return match is not None

	def parse_rcon_started(self, info):
		# RCON running on 0.0.0.0:25575
		if info.is_user:
			return False
		match = re.fullmatch(r'RCON running on [\w.]+:\d+', info.content)
		return match is not None

	def parse_server_stopping(self, info):
		# Stopping server
		if info.is_user:
			return False
		return info.content == 'Stopping server'


def get_parser(parser_manager):
	return VanillaParser(parser_manager)
