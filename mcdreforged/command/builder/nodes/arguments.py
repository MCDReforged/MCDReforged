import json
from abc import ABC
from enum import Enum
from typing import Type, Iterable, Union, Optional

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.command_builder_util import DIVIDER
from mcdreforged.command.builder.common import ParseResult, CommandContext
from mcdreforged.command.builder.exception import NumberOutOfRange, EmptyText, \
	InvalidNumber, InvalidInteger, InvalidFloat, UnclosedQuotedString, IllegalEscapesUsage, \
	TextLengthOutOfRange, InvalidBoolean, InvalidEnumeration, AbstractOutOfRange
from mcdreforged.command.builder.nodes.basic import SUGGESTS_CALLBACK, \
	ArgumentNode
# --------------------
#   Number Arguments
# --------------------
from mcdreforged.utils import misc_util


class NumberNode(ArgumentNode, ABC):
	"""
	The base class of all number related argument nodes

	It's inherited by :class:`Number`, :class:`Integer` and :class:`Float`. It represents a type of number based node

	For a :class:`NumberNode` instance, you can restrict the range of the parsed number value.
	If the parsed number is out of range,
	a :class:`~mcdreforged.command.builder.exception.NumberOutOfRange` exception will be risen

	By default, there's no range restriction
	"""

	NumberType = Union[int, float]

	def __init__(self, name):
		super().__init__(name)
		self.__min_value: Optional[NumberNode.NumberType] = None
		self.__max_value: Optional[NumberNode.NumberType] = None

	def at_min(self, min_value: NumberType) -> 'NumberNode':
		"""
		Set the lower boundary of the value range restriction. The boundary is inclusive

		:param min_value: the lower boundary of the range restriction
		"""
		self.__min_value = min_value
		return self

	def at_max(self, max_value: NumberType) -> 'NumberNode':
		"""
		Set the higher boundary of the value range restriction. The boundary is inclusive

		:param max_value: the higher boundary of the range restriction
		"""
		self.__max_value = max_value
		return self

	def in_range(self, min_value: NumberType, max_value: NumberType) -> 'NumberNode':
		"""
		Set the lower and the higher boundary of the value range restriction at the same time

		The valid value range will be ``[min_value, max_value]``, i.e. inclusive

		.. seealso::

			:meth:`at_min`, :meth:`at_max`

		:param min_value: the lower boundary of the range restriction
		:param max_value: the higher boundary of the range restriction
		"""
		self.at_min(min_value)
		self.at_max(max_value)
		return self

	def _check_in_range_and_return(self, value: NumberType, char_read: int):
		if (self.__min_value is not None and value < self.__min_value) or (self.__max_value is not None and value > self.__max_value):
			raise NumberOutOfRange(char_read, value, self.__min_value, self.__max_value)
		return ParseResult(value, char_read)

	def __str__(self):
		if self.__min_value is not None or self.__max_value is not None:
			extra = ' within [{}, {}]'.format(AbstractOutOfRange.get_boundary_text(self.__min_value), AbstractOutOfRange.get_boundary_text(self.__max_value))
		else:
			extra = ''
		return super().__str__() + extra

	def __repr__(self):
		return '{}[name={},min={},max={}]'.format(self.__class__.__name__, self.get_name(), self.__min_value, self.__max_value)


class Number(NumberNode):
	"""
	An integer, or a float

	If the next element is not a number,
	a :class:`~mcdreforged.command.builder.exception.InvalidNumber` exception will be risen
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
	An integer

	If the next element is not an integer,
	a :class:`~mcdreforged.command.builder.exception.InvalidInteger` exception will be risen
	"""
	def parse(self, text: str) -> ParseResult:
		value, read = utils.get_int(text)
		if value is not None:
			return self._check_in_range_and_return(value, read)
		else:
			raise InvalidInteger(read)


class Float(NumberNode):
	"""
	A float

	If the next element is not a float,
	a :class:`~mcdreforged.command.builder.exception.InvalidFloat` exception will be risen
	"""
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
	"""
	It's an abstract class. It's inherited by :class:`Text`, :class:`QuotableText` and :class:`GreedyText`.
	It represents a type of text based node

	For a :class:`TextNode` instance, you can restrict the length range of the parsed text.
	If the length of the parsed text is out of range,
	a :class:`~mcdreforged.command.builder.exception.TextLengthOutOfRange` exception will be risen

	By default, there's no length range restriction
	"""
	def __init__(self, name):
		super().__init__(name)
		self.__min_length = None
		self.__max_length = None

	def at_min_length(self, min_length: int) -> 'TextNode':
		"""
		Set the lower boundary of the length range restriction. The boundary is inclusive

		:param min_length: the lower boundary of the length range restriction
		"""
		self.__min_length = min_length
		return self

	def at_max_length(self, max_length: int) -> 'TextNode':
		"""
		Set the higher boundary of the length range restriction. The boundary is inclusive

		:param max_length: the higher boundary of the length range restriction
		"""
		self.__max_length = max_length
		return self

	def in_length_range(self, min_length: int, max_length: int) -> 'TextNode':
		"""
		Set the lower and the higher boundary of the length range restriction at the same time

		The valid length range will be ``[min_length, max_length]``, i.e. inclusive

		.. seealso::

			:meth:`at_min_length`, :meth:`at_max_length`

		:param min_length: the lower boundary of the length range restriction
		:param max_length: the higher boundary of the length range restriction
		"""
		self.__min_length = min_length
		self.__max_length = max_length
		return self

	def _check_length_in_range_and_return(self, text: str, char_read: int):
		length = len(text)
		if (self.__min_length is not None and length < self.__min_length) or (self.__max_length is not None and length > self.__max_length):
			raise TextLengthOutOfRange(char_read, length, self.__min_length, self.__max_length)
		return ParseResult(text, char_read)

	def __str__(self):
		if self.__min_length is not None or self.__max_length is not None:
			extra = ' in length [{}, {}]'.format(AbstractOutOfRange.get_boundary_text(self.__min_length), AbstractOutOfRange.get_boundary_text(self.__max_length))
		else:
			extra = ''
		return super().__str__() + extra

	def __repr__(self):
		return '{}[name={},min_len={},max_len={}]'.format(self.__class__.__name__, self.get_name(), self.__min_length, self.__max_length)


class Text(TextNode):
	"""
	A text argument with no space character

	It will keep reading chars continuously until it meets a space character
	"""
	def parse(self, text: str) -> ParseResult:
		arg = utils.get_element(text)
		return self._check_length_in_range_and_return(arg, len(arg))


class QuotableText(Text):
	"""
	A text argument with support for inputting space characters

	It works just like a :class:`Text` argument node, but it gives user a way
	to input text with space character: Use two double quotes to enclose the text content

	If you use two double quotes to enclose the text content, You can use escape character ``\\``
	to escape double quotes ``"`` and escape character ``\\`` itself

	For example, here are some texts that are accepted by :class:`QuotableText`:

	* ``Something``
	* ``"Something with space characters"``
	* ``"or escapes \\ like \" this"``
	"""
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
	def suggests(self, suggestion: SUGGESTS_CALLBACK) -> 'QuotableText':
		def quote_wrapper(*args, **kwargs):
			suggestions = []
			for s in suggestion(*args, **kwargs):
				if DIVIDER in s:
					s = json.dumps(s)
				suggestions.append(s)
			return suggestions

		# noinspection PyTypeChecker
		return super().suggests(misc_util.copy_signature(quote_wrapper, suggestion))


class GreedyText(TextNode):
	"""
	A text argument that consumes all remaining input

	Its principle is quite simple: It greedily takes out all remaining texts in the commands

	It's not a smart decision to append any child nodes to a :class:`GreedyText`, since the child nodes can never get any remaining command
	"""
	def parse(self, text: str) -> ParseResult:
		return self._check_length_in_range_and_return(text, len(text))


# -------------------
#   Other Arguments
# -------------------

class Boolean(ArgumentNode):
	"""
	A simple boolean argument, only accepts ``true`` and ``false``, and store them as the corresponding bool value. Case is ignored

	Raises :class:`~mcdreforged.command.builder.exception.InvalidBoolean` if the input is not accepted

	.. versionadded:: v2.3.0
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

	An Enum class is required as the parameter to its constructor

	Raises :class:`~mcdreforged.command.builder.exception.InvalidEnumeration`
	if the input argument is not a valid name for the given enum class

	Example usage::

		class MyColor(Enum):
			red = 'red color'
			blue = 'blue color'
			green = 'green color'

		node = Enumeration('arg', MyColor)

	.. versionadded:: v2.3.0
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

	def __str__(self):
		return super().__str__() + ' @ {}'.format(self.__class__.__name__, self.get_name(), self.__enum_class.__name__)

	def __repr__(self):
		return '{}[name={},enum_class={}]'.format(self.__class__.__name__, self.get_name(), self.__enum_class)

