# -*- coding: utf-8 -*-

import re
from utils.parser import base_parser


class PaperParser(base_parser.BaseParser):
	STOP_COMMAND = 'stop'

	@staticmethod
	def parse_server_stdout(text):
		result = super(PaperParser, PaperParser).parse_server_stdout(text)

		# [09:00:01 INFO]: <Steve> hi
		# [09:00:03 WARN]: Alex moved too quickly!
		try:
			time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9]* \w*\]: ', text).group()
			elements = time_data[1:-2].split(':')
			result.hour = int(elements[0])
			result.min = int(elements[1])
			result.sec = int(elements[2].split(' ')[0])
		except:
			result.content = text
		else:
			text = text.replace(time_data, '')
			# <Steve> hi
			# Alex moved too quickly!

			result.player = re.match(r'<\w+> ', text)
			if result.player is None:
				result.content = text
			else:
				result.player = result.player.group()[1:-2]
				result.content = text.replace(f'<{result.player}> ', '', 1)
		return result

	@staticmethod
	def parse_player_joined(info):
		# Fallen_Breath[/127.0.0.1:50099] logged in with entity id 11 at ([lobby]0.7133817548136454, 4.0, 5.481879061970788)
		if not info.is_user:
			result = re.fullmatch(f'\w+\[.*\] logged in with entity id .*', info.content)
			if result is not None:
				player = info.content.split('[')[0]
				return player
		return None

	@staticmethod
	def parse_player_left(info):
		if not info.is_user and info.content.endswith('left the game'):
			player = info.content.split(' ')[0]
			return player
		return None


parser = PaperParser
