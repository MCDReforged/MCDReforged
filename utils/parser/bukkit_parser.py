# -*- coding: utf-8 -*-

import os
import re
from utils.parser import vanilla_parser


class BukkitParser(vanilla_parser.VanillaParser):
	NAME = os.path.basename(__file__).rstrip('.py')

	def parse_server_stdout(self, text):
		result = self.parse_server_stdout_raw(text)

		# [09:00:01 INFO]: <Steve> hi
		# [09:00:03 WARN]: Alex moved too quickly!
		# [09:00:04 INFO]: [world_nether]<Alex> hello
		time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9]* \w*\]: ', text).group()
		elements = time_data[1:-2].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.sec = int(elements[2].split(' ')[0])
		result.logging_level = re.search(r'(?<= )\w+(?=\])', elements[2]).group()

		text = text.replace(time_data, '', 1)
		# <Steve> hi
		# Alex moved too quickly!
		# [world_nether]<Alex> hello

		dim = re.match(r'\[\w+\](?=<\w+> )', text)
		if dim is not None:
			text = text.replace(dim.group(), '', 1)
		# <Steve> hi
		# Alex moved too quickly!
		# <Alex> hello

		result.player = re.match(r'<\w+> ', text)
		if result.player is None:
			result.content = text
		else:
			result.player = result.player.group()[1:-2]
			result.content = text.replace(f'<{result.player}> ', '', 1)
		return result

	def parse_player_joined(self, info):
		# Fallen_Breath[/127.0.0.1:50099] logged in with entity id 11 at ([lobby]0.7133817548136454, 4.0, 5.481879061970788)
		if not info.is_user:
			result = re.fullmatch(f'\w+\[.*\] logged in with entity id .*', info.content)
			if result is not None:
				player = info.content.split('[')[0]
				return player
		return None


def get_parser(parser_manager):
	return BukkitParser(parser_manager)

print(BukkitParser.NAME)
