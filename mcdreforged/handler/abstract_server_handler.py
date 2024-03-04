import functools
import re
import time
from abc import ABC
from typing import List, Union, Iterable

import parse
from typing_extensions import override

from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.info_reactor.info import InfoSource, Info
from mcdreforged.utils import string_util


class AbstractServerHandler(ServerHandler, ABC):
	"""
	The abstract base class for server handler, with some common implementations
	"""
	@override
	def get_name(self) -> str:
		return string_util.hump_to_underline(type(self).__name__)

	@override
	def pre_parse_server_stdout(self, text: str) -> str:
		return text

	@override
	def parse_console_command(self, text: str) -> Info:
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
		This method does a raw parsing and returns an almost un-parsed :class:`~mcdreforged.info_reactor.info.Info` object

		Use as the first step of the parsing process, or as the parsing result if you give up parsing this text

		:meta public:
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

		The return value of the first succeeded ``parse.parse`` call will be used
		for filling fields of the :class:`~mcdreforged.info_reactor.info.Info` object

		The return value should be a constant value
		"""
		raise NotImplementedError()

	@classmethod
	@functools.lru_cache()
	def _get_content_parsers(cls) -> List[parse.Parser]:
		"""
		The return value is cached for reuse. Do not modify
		"""
		formatters = cls.get_content_parsing_formatter()
		if isinstance(formatters, str):
			formatters = (formatters,)
		return list(map(parse.Parser, formatters))

	__worlds_only_regex = re.compile(r'\w+')

	@classmethod
	def _content_parse(cls, info: Info):
		"""
		A commonly used method to parse several generic elements from an un-parsed :class:`~mcdreforged.info_reactor.info.Info` object

		Elements expected to be parsed includes:

		- :attr:`info.hour <mcdreforged.info_reactor.info.Info.hour>`
		- :attr:`info.min <mcdreforged.info_reactor.info.Info.min>`
		- :attr:`info.sec <mcdreforged.info_reactor.info.Info.sec>`
		- :attr:`info.logging <mcdreforged.info_reactor.info.Info.logging>`
		- :attr:`info.content <mcdreforged.info_reactor.info.Info.content>`

		:param info: The to-be-processed :class:`~mcdreforged.info_reactor.info.Info` object
		:meta public:
		"""
		for parser in cls._get_content_parsers():
			parsed = parser.parse(info.content)
			if parsed is not None:
				logging_level = parsed['logging']
				if cls.__worlds_only_regex.fullmatch(logging_level) is None:
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

	@override
	def parse_server_stdout(self, text: str) -> Info:
		info = self._get_server_stdout_raw_result(text)
		self._content_parse(info)
		return info
