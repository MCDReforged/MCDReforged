# -*- coding: utf-8 -*-
import os
import re

from utils import tool
from utils.parser.abstract_parser import AbstractParser


class VanillaParser(AbstractParser):
	NAME = tool.remove_suffix(os.path.basename(__file__), '.py')
	PLAYER_JOINED_PATTERN = re.compile(r'\w{1,16}\[/[\d.:a-z]+\] logged in with entity id \d+ at \([\dE\-., ]+\)')
	STOP_COMMAND = 'stop'
	LOGGER_NAME_CHAR_SET = r'\w /\#\-'

	def parse_server_stdout(self, text):
		result = self.__parse_server_stdout_raw(text)

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
		logging = re.match(r'^\[[{}]*?\]: '.format(self.LOGGER_NAME_CHAR_SET), text).group()
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
		# Steve[/127.0.0.1:9864] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
		if not info.is_user and self.PLAYER_JOINED_PATTERN.fullmatch(info.content):
			return info.content.split('[', 1)[0]
		return None

	def parse_player_left(self, info):
		# Steve left the game
		if not info.is_user and re.fullmatch(r'\w{1,16} left the game', info.content):
			return info.content.split(' ')[0]
		return None

	def parse_player_made_advancement(self, info):
		# Steve has made the advancement [Stone Age]
		# Steve has completed the challenge [Uneasy Alliance]
		# Steve has reached the goal [Sky's the Limit]
		if info.is_user:
			return None
		for action in ['made the advancement', 'completed the challenge', 'reached the goal']:
			match = re.fullmatch(r'\w{1,16} has %s \[.+\]' % action, info.content)
			if match is not None:
				player, rest = info.content.split(' ', 1)
				adv = re.search(r'(?<=%s \[).+(?=\])' % action, rest).group()
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
