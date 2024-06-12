import functools
import re
import time
from abc import ABC
from typing import List, Union, Iterable

import parse
from typing_extensions import override

from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.info_reactor.info import InfoSource, Info
from mcdreforged.utils import string_utils


class AbstractServerHandler(ServerHandler, ABC):
	"""
	The abstract base class for server handler, with some common implementations
	"""
	@override
	def get_name(self) -> str:
		return string_utils.hump_to_underline(type(self).__name__)

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
		result.content = string_utils.clean_console_color_code(text)
		return result

	@classmethod
	def get_content_parsing_formatter(cls) -> Union[str, Iterable[str]]:
		"""
		Return a :external:class:`re.Pattern` or an Iterable of :external:class:`re.Pattern` iterable
		that is used in method :meth:`_content_parse` for parsing

		These regex patterns are supposed to contain at least the following fields:

		- ``hour``
		- ``min``
		- ``sec``
		- ``logging``
		- ``content``

		The return value of the first succeeded :external:meth:`re.Pattern.fullmatch` call will be used
		for filling fields of the :class:`~mcdreforged.info_reactor.info.Info` object

		The return value should be a constant value
		"""
		raise NotImplementedError()

	@classmethod
	@functools.lru_cache()
	def __get_content_parsers(cls) -> List[re.Pattern]:
		"""
		The return value is cached for reuse. Do not modify
		"""
		# TODO: drop parse.Parser support
		formatters = cls.get_content_parsing_formatter()
		if isinstance(formatters, str) or isinstance(formatters, re.Pattern):
			formatters = [formatters]
		return [parse.Parser(fmt) if isinstance(fmt, str) else fmt for fmt in formatters]

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
		for parser in cls.__get_content_parsers():
			# TODO: drop parse.Parser support
			if isinstance(parser, parse.Parser):
				parsed = parser.parse(info.content)
			else:
				parsed = parser.fullmatch(info.content)
			if parsed is not None:
				break
		else:
			raise ValueError('Unrecognized input: ' + info.content)

		info.hour = int(parsed['hour'])
		info.min = int(parsed['min'])
		info.sec = int(parsed['sec'])
		info.logging_level = parsed['logging']
		info.content = parsed['content']

	@override
	def parse_server_stdout(self, text: str) -> Info:
		info = self._get_server_stdout_raw_result(text)
		self._content_parse(info)
		return info
