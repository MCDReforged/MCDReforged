import os
import re

from utils import tool, constant
from utils.parser.vanilla_parser import VanillaParser


class BukkitParser(VanillaParser):
	NAME = tool.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)

	# Fallen_Breath[/127.0.0.1:50099] logged in with entity id 11 at ([lobby]0.7133817548136454, 4.0, 5.481879061970788)
	# Fake_player[local] logged in with entity id 11 at ([lobby]100.19, 22.33, 404.0)
	PLAYER_JOINED_PATTERN = re.compile(r'\w{1,16}\[(?:/[\d.:]+|local)\] logged in with entity id \d+ at \((\[\w+\])?[\dE\-., ]+\)')

	def parse_server_stdout(self, text):
		result = self._parse_server_stdout_raw(text)

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


def get_parser(parser_manager):
	return BukkitParser(parser_manager)

