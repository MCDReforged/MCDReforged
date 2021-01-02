import os
import re

from mcdr import tool, constant
from mcdr.parser.vanilla_parser import VanillaParser


class ForgeParser(VanillaParser):
	NAME = tool.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)
	LOGGER_NAME_CHAR_SET = VanillaParser.LOGGER_NAME_CHAR_SET + r'.'

	def __init__(self, parser_manager):
		super().__init__(parser_manager)

	def parse_server_stdout(self, text):
		result = self._parse_server_stdout_raw(text)

		# [18:26:03] [Server thread/INFO] [FML]: Unloading dimension 1
		# [18:26:03] [Server thread/INFO] [minecraft/DedicatedServer]: Done (9.855s)! For help, type "help" or "?"
		# [18:29:30] [Server thread/INFO] [minecraft/DedicatedServer]: <Steve> tests
		time_data = re.search(r'\[[0-9]*:[0-9]*:[0-9.]*\] ', text).group()
		elements = time_data[1:-2].split(':')
		result.hour = int(elements[0])
		result.min = int(elements[1])
		result.sec = int(float(elements[2]))

		text = text.replace(time_data, '', 1)
		# [Server thread/INFO] [FML]: Unloading dimension 1
		# [Server thread/INFO] [minecraft/DedicatedServer]: Done (9.855s)! For help, type "help" or "?"
		# [Server thread/INFO] [minecraft/DedicatedServer]: <Steve> tests

		logging = re.match(r'^\[[{}]*?\] '.format(self.LOGGER_NAME_CHAR_SET), text).group()
		result.logging_level = re.search(r'(?<=/)\w+(?=\] )', logging).group()
		text = text.replace(logging, '', 1)
		# [FML]: Unloading dimension 1
		# [minecraft/DedicatedServer]: Done (9.855s)! For help, type "help" or "?"
		# [minecraft/DedicatedServer]: <Steve> tests

		matched = re.match(r'^\[[{}]*\]: '.format(self.LOGGER_NAME_CHAR_SET), text).group()
		text = text.replace(matched, '', 1)
		# Unloading dimension 1
		# Done (9.855s)! For help, type "help" or "?"
		# <Steve> tests

		result.player = re.match(r'<\w+> ', text)
		if result.player is None:
			result.content = text
		else:
			result.player = result.player.group()[1:-2]
			result.content = text.replace(f'<{result.player}> ', '', 1)
		return result


def get_parser(parser_manager):
	return ForgeParser(parser_manager)
