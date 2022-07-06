import json
from abc import ABC
from enum import Enum
from typing import Type, Iterable, Union

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.command_builder_util import DIVIDER
from mcdreforged.command.builder.common import ParseResult, CommandContext
from mcdreforged.command.builder.exception import NumberOutOfRange, EmptyText, \
	InvalidNumber, InvalidInteger, InvalidFloat, UnclosedQuotedString, IllegalEscapesUsage, \
	TextLengthOutOfRange, InvalidBoolean, InvalidEnumeration
from mcdreforged.command.builder.nodes.basic import AbstractNode, SUGGESTS_CALLBACK, \
	ArgumentNode
# --------------------
#   Number Arguments
# --------------------
from mcdreforged.utils import misc_util


class NumberNode(ArgumentNode, ABC):
	def __init__(self, name):
		super().__init__(name)
		self.__min_value = None
		self.__max_value = None

	def at_min(self, min_value) -> 'NumberNode':
		self.__min_value = min_value
		return self

	def at_max(self, max_value) -> 'NumberNode':
		self.__max_value = max_value
		return self

	def in_range(self, min_value, max_value) -> 'NumberNode':
		self.at_min(min_value)
		self.at_max(max_value)
		return self

	def _check_in_range_and_return(self, value: Union[int, float], char_read: int):
		if (self.__min_value is not None and value < self.__min_value) or (self.__max_value is not None and value > self.__max_value):
			raise NumberOutOfRange(char_read, value, self.__min_value, self.__max_value)
		return ParseResult(value, char_read)


class Number(NumberNode):
	"""
	An Integer, or a float
	"""
	def parse(self, text: str) -> ParseResult:
		value, read = utils.get_int(text)
		if value is None:
			value, read = utils.get_float(text)
		if value is not None:
			return self._check_in_range_and_return(value, read)
		else:
			raise InvalidNumber(read)


class Integer(NumberNode):
	"""
	An Integer
	"""
	def parse(self, text: str) -> ParseResult:
		value, read = utils.get_int(text)
		if value is not None:
			return self._check_in_range_and_return(value, read)
		else:
			raise InvalidInteger(read)


class Float(NumberNode):
	def parse(self, text: str) -> ParseResult:
		value, read = utils.get_float(text)
		if value is not None:
			return self._check_in_range_and_return(value, read)
		else:
			raise InvalidFloat(read)

# ------------------
#   Text Arguments
# ------------------


class TextNode(ArgumentNode, ABC):
	def __init__(self, name):
		super().__init__(name)
		self.__min_length = None
		self.__max_length = None

	def at_min_length(self, min_length) -> 'TextNode':
		self.__min_length = min_length
		return self

	def at_max_length(self, max_length) -> 'TextNode':
		self.__max_length = max_length
		return self

	def in_length_range(self, min_length, max_length) -> 'TextNode':
		self.__min_length = min_length
		self.__max_length = max_length
		return self

	def _check_length_in_range_and_return(self, text: str, char_read: int):
		length = len(text)
		if (self.__min_length is not None and length < self.__min_length) or (self.__max_length is not None and length > self.__max_length):
			raise TextLengthOutOfRange(char_read, length, self.__min_length, self.__max_length)
		return ParseResult(text, char_read)


class Text(TextNode):
	"""
	A text argument with no space character
	Just like a single word
	"""
	def parse(self, text: str) -> ParseResult:
		arg = utils.get_element(text)
		return self._check_length_in_range_and_return(arg, len(arg))


class QuotableText(Text):
	QUOTE_CHAR = '"'
	ESCAPE_CHAR = '\\'

	def __init__(self, name):
		super().__init__(name)
		self.empty_allowed = False

	def allow_empty(self):
		self.empty_allowed = True
		return self

	def parse(self, text: str) -> ParseResult:
		if len(text) == 0 or text[0] != self.QUOTE_CHAR:
			return super().parse(text)  # regular text
		collected = []
		i = 1
		escaped = False
		while i < len(text):
			ch = text[i]
			if escaped:
				if ch == self.ESCAPE_CHAR or ch == self.QUOTE_CHAR:
					collected.append(ch)
					escaped = False
				else:
					raise IllegalEscapesUsage(i + 1)
			elif ch == self.ESCAPE_CHAR:
				escaped = True
			elif ch == self.QUOTE_CHAR:
				result = ''.join(collected)
				if not self.empty_allowed and len(result) == 0:
					raise EmptyText(i + 1)
				return self._check_length_in_range_and_return(result, i + 1)
			else:
				collected.append(ch)
			i += 1
		raise UnclosedQuotedString(text)

	# use quote characters to quote suggestions with DIVIDER
	def suggests(self, suggestion: SUGGESTS_CALLBACK) -> 'AbstractNode':
		def quote_wrapper(*args, **kwargs):
			suggestions = []
			for s in suggestion(*args, **kwargs):
				if DIVIDER in s:
					s = json.dumps(s)
				suggestions.append(s)
			return suggestions
		return super().suggests(misc_util.copy_signature(quote_wrapper, suggestion))


class GreedyText(TextNode):
	"""
	A greedy text argument, which will consume all remaining input
	"""
	def parse(self, text: str) -> ParseResult:
		return self._check_length_in_range_and_return(text, len(text))


# -------------------
#   Other Arguments
# -------------------

class Boolean(ArgumentNode):
	"""
	A simple boolean argument, only accepts ``true`` and ``false`` and store them as a bool. Case is ignored
	"""
	def _get_suggestions(self, context: CommandContext) -> Iterable[str]:
		return ['true', 'false']

	def parse(self, text: str) -> ParseResult:
		arg = utils.get_element(text)
		if arg.lower() == 'true':
			value = True
		elif arg.lower() == 'false':
			value = False
		else:
			raise InvalidBoolean(arg)
		return ParseResult(value, len(arg))


class Enumeration(ArgumentNode):
	"""
	A node associating with an Enum class for reading an enum value of the given class
	"""
	def __init__(self, name: str, enum_class: Type[Enum]):
		super().__init__(name)
		self.__enum_class: Type[Enum] = enum_class

	def _get_suggestions(self, context: CommandContext) -> Iterable[str]:
		return map(lambda e: e.name, self.__enum_class)

	def parse(self, text: str) -> ParseResult:
		arg = utils.get_element(text)
		try:
			enum = self.__enum_class[arg]
		except KeyError:
			raise InvalidEnumeration(arg) from None
		else:
			return ParseResult(enum, len(arg))


