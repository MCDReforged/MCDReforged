# -*- coding: utf-8 -*-

import re
from utils.parser import base_parser


class VanillaParser(base_parser.BaseParser):
	STOP_COMMAND = 'stop'

	@staticmethod
	def parse_server_stdout(text):
		result = super(VanillaParser, VanillaParser).parse_server_stdout(text)

		# [09:00:00] [Server thread/INFO]: <Steve> Hello
		# [09:00:01] [Server thread/WARN]: Can't keep up!
		time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9]*\] ', text).group()
		elements = time_data[1:-2].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.second = int(elements[2])

		text = text.replace(time_data, '')
		# [Server thread/INFO]: <Steve> Hello
		# [Server thread/WARN]: Can't keep up!

		text = re.split(r'\[[\w /]*\]: ', text)[1]
		# <Steve> Hello
		# Can't keep up!

		result.player = re.match(r'<\w+> ', text)
		if result.player is None:
			result.content = text
		else:
			result.player = result.player.group()[1:-2]
			result.content = text.replace(f'<{result.player}> ', '', 1)
		return result


parser = VanillaParser
