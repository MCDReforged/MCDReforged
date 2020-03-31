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
		time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9]* \w*\]: ', text).group()
		elements = time_data[1:-2].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.second = int(elements[2].split(' ')[0])

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


parser = PaperParser
