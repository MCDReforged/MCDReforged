import re
import time
from typing import Optional, Any

from parse import parse

from mcdreforged.info import InfoSource, Info
from mcdreforged.utils import string_util

'''
AbstractServerHandler
 ├─ BasicHandler
 ├─ VanillaHandler
 │   ├─ BukkitHandler
 │   │   ├─ Bukkit14Handler
 │   │   └─ CatServerHandler
 │   ├─ ForgeHandler
 │   └─ Beta18Handler
 └─ BungeecordHandler
     └─ WaterfallHandler
'''


class AbstractServerHandler:
	# ---------------------
	#   Basic Information
	# ---------------------

	def get_name(self) -> str:
		return string_util.hump_to_underline(type(self).__name__)

	# ------------------
	#   Server control
	# ------------------

	def get_stop_command(self) -> str:
		"""
		The command to stop the server
		"""
		raise NotImplementedError()

	def get_send_message_command(self, target: str, message: Any) -> Optional[str]:
		"""
		The command to send a message to a target
		"""
		raise NotImplementedError()

	def get_broadcast_message_command(self, message: Any) -> Optional[str]:
		"""
		The command to broadcast a message in the server
		"""
		raise NotImplementedError()

	# -------------------------
	#   Server output parsing
	# -------------------------

	def pre_parse_server_stdout(self, text: str) -> str:
		"""
		Remove useless / annoying things like control characters in the text before parse

		:param str text: A line of the server stdout to be parsed
		:rtype: str
		"""
		return text

	@classmethod
	def parse_console_command(cls, text: str) -> Info:
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

	@classmethod
	def _get_server_stdout_raw_result(cls, text: str) -> Info:
		"""
		This is a raw parsing, returns an almost un-parsed Info instance
		Use as the first step of the parsing process, or as the return value if you give up parsing this text
		"""
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info()
		result.source = InfoSource.SERVER
		result.raw_content = text
		result.content = string_util.clean_console_color_code(text)
		return result

	@classmethod
	def get_content_parsing_formatter(cls):
		raise NotImplementedError()

	@classmethod
	def _content_parse(cls, info: Info, *, formatter=None):
		if formatter is None:
			formatter = cls.get_content_parsing_formatter()
		parsed = parse(formatter, info.content)
		info.hour = parsed['hour']
		info.min = parsed['min']
		info.sec = parsed['sec']
		info.logging_level = parsed['logging']
		assert re.fullmatch(r'\w+', info.logging_level) is not None  # logging level should be text only, just in case
		info.content = parsed['content']

	def parse_server_stdout(self, text: str) -> Info:
		"""
		Main parsing operation. Parse a string from the stdout of the server
		It may raise any exceptions if the format of the input string is not correct

		In this implementation it achieves raw parsing, returns an almost un-parsed Info instance
		Use as the first step of the parsing process, or as the return value if you give up parsing this text
		:param str text: A line of the server stdout to be parsed
		:return: An Info instance
		:rtype: Info
		"""
		raise NotImplementedError()

	def parse_player_joined(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicating a player joined message
		If it is, returns the name of the player, otherwise returns None

		:param Info info: The info instance that will be checked
		:return: The name of the player or None
		:rtype: str or None
		"""
		raise NotImplementedError()

	def parse_player_left(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicates a player left message
		If it is, returns the name of the player, otherwise returns None

		:param Info info: The info instance that will be checked
		:return: The name of the player or None
		:rtype: str or None
		"""
		raise NotImplementedError()

	def test_server_startup_done(self, info: Info) -> bool:
		"""
		Check if the info indicates a server startup message and return a bool

		:param Info info: The info instance that will be checked
		:return: If the info indicates a server startup message
		:rtype: bool
		"""
		raise NotImplementedError()

	def test_rcon_started(self, info: Info) -> bool:
		"""
		Check if rcon has started and return a bool

		:param Info info: The info instance that will be checked
		:return: If rcon has started
		:rtype: bool
		"""
		raise NotImplementedError()

	def test_server_stopping(self, info: Info) -> bool:
		"""
		Check if the server is stopping and return a bool

		:param Info info: The info instance that will be checked
		:return: If the server is stopping
		:rtype: bool
		"""
		raise NotImplementedError()
