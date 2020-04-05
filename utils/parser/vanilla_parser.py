# -*- coding: utf-8 -*-

import re
from utils.parser import base_parser


class VanillaParser(base_parser.BaseParser):
	def __init__(self):
		super().__init__()
		self.STOP_COMMAND = 'stop'
		self.Logger_NAME_CHAR_SET = r'\w /'

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

		text = re.split(r'\[[{}]*?\]: '.format(self.Logger_NAME_CHAR_SET), text)[1]
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
		if not info.is_user and info.content.endswith('joined the game'):
			player = info.content.split(' ')[0]
			return player
		return None

	def parse_player_left(self, info):
		if not info.is_user and info.content.endswith('left the game'):
			player = info.content.split(' ')[0]
			return player
		return None

	def is_server_startup_done(self, info):
		# Done (3.500s)! For help, type "help"
		if info.is_user:
			return False
		match = re.match(r'Done \([0-9.]*s\)! For help, type "help"', info.content)
		return match is not None


parser = VanillaParser()
