import re
import time
from typing import Optional, Any, Union, Iterable, Tuple

from parse import parse

from mcdreforged.info_reactor.info import InfoSource, Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils import string_util


class AbstractServerHandler:
	"""
	The abstract base class for server handler

	Class inheriting tree::

		AbstractServerHandler
		├── BasicHandler
		├── AbstractMinecraftHandler
		│   ├── VanillaHandler
		│   │   ├── Beta18Handler
		│   │   └── ForgeHandler
		│   └── BukkitHandler
		│       ├── Bukkit14Handler
		│       └── CatServerHandler
		├── BungeecordHandler
		│   └── WaterfallHandler
		└── VelocityHandler
	"""

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

	def get_send_message_command(self, target: str, message: Any, server_information: ServerInformation) -> Optional[str]:
		"""
		The command to send a message to a target
		"""
		raise NotImplementedError()

	def get_broadcast_message_command(self, message: Any, server_information: ServerInformation) -> Optional[str]:
		"""
		The command to broadcast a message in the server
		"""
		raise NotImplementedError()

	# -------------------------
	#   Server output parsing
	# -------------------------

	def pre_parse_server_stdout(self, text: str) -> str:
		"""
		A parsing preprocessor. Invoked before any parsing operation

		Remove useless / annoying things like control characters in the text before parsing

		:param text: A line of the server stdout to be parsed
		"""
		return text

	@classmethod
	def parse_console_command(cls, text: str) -> Info:
		"""
		Parse console input

		:param text: A line of console input to be parsed
		:return: An :class:`~mcdreforged.info_reactor.info.Info` object as the result
		"""
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info(InfoSource.CONSOLE, text)
		t = time.localtime(time.time())
		result.hour = t.tm_hour
		result.min = t.tm_min
		result.sec = t.tm_sec
		result.content = text
		return result

	@classmethod
	def _get_server_stdout_raw_result(cls, text: str) -> Info:
		"""
		This is a raw parsing, returns an almost un-parsed Info instance

		Use as the first step of the parsing process, or as the return value if you give up parsing this text
		"""
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		result = Info(InfoSource.SERVER, text)
		result.content = string_util.clean_console_color_code(text)
		return result

	@classmethod
	def get_content_parsing_formatter(cls) -> Union[str, Iterable[str]]:
		"""
		Return a str or a str iterable that is used in method :meth:`_content_parse` for parsing

		These strings will be passed as the 1st parameter to ``parse.parse``,
		they are both supposed to contain at least the following fields:

		- ``hour``
		- ``min``
		- ``sec``
		- ``logging``
		- ``content``
		"""
		raise NotImplementedError()

	@classmethod
	def _content_parse(cls, info: Info):
		"""
		A common method to parse several elements from an un-parsed Info instance

		Elements expected to be parsed includes:
		- info.hour
		- info.min
		- info.sec
		- info.logging
		- info.content

		:param info: The to-be-processed :class:`~mcdreforged.info_reactor.info.Info` object
		"""
		formatters = cls.get_content_parsing_formatter()
		if isinstance(formatters, str):
			formatters = (formatters,)
		for formatter in formatters:
			parsed = parse(formatter, info.content)
			if parsed is not None:
				logging_level = parsed['logging']
				if re.fullmatch(r'\w+', logging_level) is None:
					# logging level should be text only, just in case
					# might happen in e.g. WaterfallHandler parsing "[01:23:45 INFO] [Test]: ping"
					continue
				break
		else:
			raise ValueError('Unrecognized input: ' + info.content)
		info.hour = parsed['hour']
		info.min = parsed['min']
		info.sec = parsed['sec']
		info.logging_level = parsed['logging']
		info.content = parsed['content']

	def parse_server_stdout(self, text: str) -> Info:
		"""
		Main parsing operation. Parse a string from the stdout of the server
		It may raise any exceptions if the format of the input string is not correct

		In this implementation it achieves raw parsing, returns an almost un-parsed Info instance
		Use as the first step of the parsing process, or as the return value if you give up parsing this text

		:param str text: A line of the server stdout to be parsed
		:return: An :class:`~mcdreforged.info_reactor.info.Info` object as the result
		"""
		result = self._get_server_stdout_raw_result(text)
		self._content_parse(result)
		return result

	def parse_player_joined(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicating a player joined message

		If it is, returns the name of the player, otherwise returns None

		:param info: The info object to be checked
		:return: The name of the player, or None
		"""
		raise NotImplementedError()

	def parse_player_left(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicates a player left message

		If it is, returns the name of the player, otherwise returns None

		:param info: The info object to be checked
		:return: The name of the player, or None
		"""
		raise NotImplementedError()

	def parse_server_version(self, info: Info) -> Optional[str]:
		"""
		Check if the info contains a server version message

		If it is, returns server version, otherwise returns None

		:param info: The info object to be checked
		:return: The version of the server, or None
		"""
		raise NotImplementedError()

	def parse_server_address(self, info: Info) -> Optional[Tuple[str, int]]:
		"""
		Check if the info contains the address which the server is listening on

		If it is, returns server ip and port, otherwise returns None

		:param info: The info object to be checked
		:return: A tuple containing the ip and the port, or None
		"""
		raise NotImplementedError()

	def test_server_startup_done(self, info: Info) -> bool:
		"""
		Check if the info indicates a server startup message

		:param info: The info object to be checked
		:return: If the info indicates a server startup message
		"""
		raise NotImplementedError()

	def test_rcon_started(self, info: Info) -> bool:
		"""
		Check if rcon has started

		:param info: The info object to be checked
		:return: If rcon has started
		"""
		raise NotImplementedError()

	def test_server_stopping(self, info: Info) -> bool:
		"""
		Check if the server is stopping

		:param info: The info object to be checked
		:return: If the server is stopping
		"""
		raise NotImplementedError()
