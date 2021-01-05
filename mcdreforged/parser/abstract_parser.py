import os
import re
import time

from mcdreforged import constant
from mcdreforged.info import InfoSource, Info
from mcdreforged.utils import string_util

'''
AbstractParser
 ├─ BaseParser
 ├─ VanillaParser
 │   ├─ BukkitParser
 │   │   └─ CatServerParser
 │   ├─ BukkitParser14
 │   └─ ForgeParser
 └─ BungeecordParser
     └─ WaterfallParser
'''


class AbstractParser:
	NAME = string_util.remove_suffix(os.path.basename(__file__), constant.PARSER_FILE_SUFFIX)
	STOP_COMMAND = ''

	def __init__(self, parser_manager):
		self.parser_manager = parser_manager

	@staticmethod
	def _parse_server_stdout_raw(text: str):
		"""
		Base raw parsing, returns an almost un-parsed Info instance
		Use as the first step of the parsing process, or as the return value if you give up parsing this text

		:param str text: A line of the server stdout to be parsed
		:return: An Info instance
		:rtype: Info
		"""
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info()
		result.source = InfoSource.SERVER
		result.content = result.raw_content = text
		return result

	def pre_parse_server_stdout(self, text):
		"""
		Remove useless things like console color code in the text before parse

		:param str text: A line of the server stdout to be parsed
		:return: Trimmed line
		:rtype: str
		"""
		return string_util.clean_console_color_code(text)

	@staticmethod
	def parse_console_command(text):
		"""
		Base parsing, returns an almost un-parsed Info instance
		Don't use this unless

		:param str text: A line of the server stdout to be parsed
		:return: An Info instance
		:rtype: Info
		"""
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info()
		result.raw_content = text
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.sec = t.tm_sec
		result.content = text
		result.source = InfoSource.CONSOLE
		return result

	def parse_death_message(self, info):
		"""
		Check if the info matches a death message and return a bool
		It will search all death message format from itself to its all base class and try to match the info with them

		:param Info info: The info instance that will be checked
		:return: If the info matches a death message
		:rtype: bool
		"""
		if info.is_user:
			return False
		re_list = self.parser_manager.get_death_message_list(type(self))
		for re_exp in re_list:
			if re.fullmatch(re_exp, info.content):
				return True
		return False

	# ----------------------------------------
	#    Things that need to be implemented
	# ----------------------------------------

	def parse_server_stdout(self, text):
		"""
		Main parsing operation. Parse a string from the stdout of the server
		It may raise any exceptions if the format of the input string is not correct

		:param str text: A line of the server stdout to be parsed
		:return: An parsed Info instance
		:rtype: Info
		"""
		raise NotImplementedError()

	def parse_player_joined(self, info):
		"""
		Check if the info indicating a player joined message
		If it is, returns the name of the player, otherwise returns None

		:param Info info: The info instance that will be checked
		:return: The name of the player or None
		:rtype: str or None
		"""
		raise NotImplementedError()

	def parse_player_left(self, info):
		"""
		Check if the info indicates a player left message
		If it is, returns the name of the player, otherwise returns None

		:param Info info: The info instance that will be checked
		:return: The name of the player or None
		:rtype: str or None
		"""
		raise NotImplementedError()

	def parse_player_made_advancement(self, info):
		"""
		Check if the info indicates a player made advancement message
		If it is, returns a tuple of two str: the name of the player and the name of the advancement, otherwise returns None

		:param Info info: The info instance that will be checked
		:return: (player_name, advancement_name), or None
		:rtype: tuple[str, str] or None
		"""
		raise NotImplementedError()

	def parse_server_startup_done(self, info):
		"""
		Check if the info indicates a server startup message and return a bool

		:param Info info: The info instance that will be checked
		:return: If the info indicates a server startup message
		:rtype: bool
		"""
		raise NotImplementedError()

	def parse_rcon_started(self, info: Info):
		"""
		Check if rcon has started and return a bool

		:param Info info: The info instance that will be checked
		:return: If rcon has started
		:rtype: bool
		"""
		raise NotImplementedError()

	def parse_server_stopping(self, info: Info):
		"""
		Check if the server is stopping and return a bool

		:param Info info: The info instance that will be checked
		:return: If the server is stopping
		:rtype: bool
		"""
		raise NotImplementedError()
