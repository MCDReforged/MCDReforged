import collections
from abc import ABC
from typing import List, Callable

__all__ = [
	# utils
	'get_element', 'get_int', 'get_float',

	# errors
	'CommandError', 'UnknownCommand', 'UnknownArgument', 'UnknownRootArgument',  # command structure errors
	'IllegalArgument', 'NumberOutOfRange', 'EmptyText',  # built-in command syntax errors

	# for custom argument type
	'CommandSyntaxError', 'ArgumentNode', 'ParseResult',

	# nodes
	'Literal',
	'Number', 'Integer', 'Float',
	'Text', 'QuotableText', 'GreedyText'
]


ParseResult = collections.namedtuple('ParseResult', 'value char_read')
DIVIDER = ' '


class CommandError(Exception):
	def __init__(self, message, fail_position_hint):
		self.message = message
		self.fail_position_hint = fail_position_hint

	def __str__(self):
		return '{}: {}'.format(self.message, self.fail_position_hint)


class UnknownCommand(CommandError):
	"""
	When the command finishes parsing, but current node doesn't have a callback function
	"""
	def __init__(self, fail_position):
		super().__init__('Unknown Command', fail_position)


class UnknownArgument(CommandError):
	"""
	When there's remaining command string, but there's no matched Literal nodes and no general argument nodes
	"""
	def __init__(self, fail_position):
		super().__init__('Unknown Argument', fail_position)


class UnknownRootArgument(UnknownArgument):
	"""
	The same as UnknownArgument, but it fails to match at root node
	"""
	pass


class CommandSyntaxError(CommandError):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	def __init__(self, message, char_read):
		super().__init__(message, 'unknown')
		self.message = message
		self.char_read = char_read

	def set_fail_position_hint(self, fail_position_hint):
		self.fail_position_hint = fail_position_hint


class IllegalArgument(CommandSyntaxError):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	pass


class IllegalLiteralArgument(CommandSyntaxError):
	"""
	Used by Literal node parsing failure for fail-soft
	"""
	pass


class NumberOutOfRange(CommandSyntaxError):
	"""
	The parsed number value is out of the restriction range
	"""
	pass


class EmptyText(CommandSyntaxError):
	"""
	The text is empty, and it's not allowed to be
	"""
	pass


def remove_divider_prefix(text):
	return text.lstrip(DIVIDER)


def get_element(text):
	"""
	"my test command" -> "my"
	:type text: str
	:rtype: str
	"""
	pos = text.find(DIVIDER)
	if pos == -1:
		return text
	else:
		return text[:pos]


def __get_var(text, func):
	"""
	Return value, char_read
	value will be None if ValueError occurs
	"""
	origin_text = text
	text = remove_divider_prefix(text)
	arg = get_element(text)
	try:
		value = func(arg)
	except ValueError:
		value = None
	return value, len(origin_text) - len(text) + len(arg)


def get_int(text):
	return __get_var(text, int)


def get_float(text):
	return __get_var(text, float)


class ArgumentNode:
	def __init__(self, name):
		self.name = name
		self.children_literal = []  # type: List[Literal]
		self.children = []  # type: List[ArgumentNode]
		self.callback = None

	# --------------
	#   Interfaces
	# --------------

	def then(self, node):
		"""
		:param ArgumentNode node: a child node for new level command
		:rtype: ArgumentNode
		"""
		if isinstance(node, Literal):
			self.children_literal.append(node)
		else:
			self.children.append(node)
		return self

	def run(self, func: Callable[[dict], None]):
		"""
		:param func: a function to execute at this node
		:rtype: ArgumentNode
		"""
		self.callback = func
		return self

	def execute(self, command):
		"""
		Parse and execute this command
		Raise variable CommandError if parsing fails
		A RuntimeError will be raised if this method is not invoked from a Literal node
		:param str command: the command string to execute
		:rtype: None
		"""
		if isinstance(self, Literal):
			try:
				self._execute(command, command, {})
			except IllegalLiteralArgument as e:
				# the root literal node fails to parse the first element
				raise UnknownRootArgument(e.fail_position_hint)
		else:
			raise RuntimeError('Only Literal node is allowed to execute a command')

	# -------------------
	#   Interfaces ends
	# -------------------

	def __does_store_thing(self):
		"""
		If this argument stores something into the context after parsing the given command string
		For example it might need to store an int after parsing an integer
		In general situation, only Literal Argument doesn't store anything
		:return: bool
		"""
		return self.name is not None

	def parse(self, text):
		"""
		Try to parse the text and get a argument. Return a ParseResult instance indicating the parsing result
		ParseResult.success: If the parsing is success
		ParseResult.value: The value to store in the context dict
		ParseResult.remaining: The remain
		:param str text: the remaining text to be parsed
		:rtype: ParseResult
		"""
		raise NotImplementedError()

	def _execute(self, command, remaining, context):
		def error_pos(ending_pos):
			return '{}<--'.format(command[:ending_pos])

		try:
			result = self.parse(remaining)
		except CommandSyntaxError as e:
			e.set_fail_position_hint(error_pos(len(command) - len(remaining) + e.char_read))
			raise e

		if self.__does_store_thing():
			context[self.name] = result.value

		total_read = len(command) - len(remaining) + result.char_read
		trimmed_remaining = remove_divider_prefix(remaining[result.char_read:])
		# Parsing finished
		if len(trimmed_remaining) == 0:
			if self.callback is not None:
				self.callback(context)
			else:
				raise UnknownCommand(error_pos(total_read))
		# Un-parsed command string remains
		else:
			# No child at all
			if len(self.children) + len(self.children_literal) == 0:
				raise UnknownArgument(error_pos(len(command)))

			for child_literal in self.children_literal:
				try:
					child_literal._execute(command, trimmed_remaining, context)
					break
				except IllegalLiteralArgument:
					# it's ok for a direct literal node to fail
					pass
			else:
				# No argument child
				if len(self.children) == 0:
					raise UnknownArgument(error_pos(len(command)))
				for child in self.children:
					try:
						child._execute(command, trimmed_remaining, context)
						break
					except IllegalArgument:
						raise

# ---------------------------------
#   Argument Node implementations
# ---------------------------------


class Literal(ArgumentNode):
	"""
	A literal argument, doesn't store any value, only for extending and readability of the command
	The only argument type that is allowed to use the execute method
	"""
	def __init__(self, literal):
		super().__init__(None)
		if ' ' in literal:
			raise TypeError('Space character cannot be inside a literal')
		self.literal = literal

	def parse(self, text):
		arg = get_element(text)
		if arg == self.literal:
			return ParseResult(None, len(arg))
		else:
			raise IllegalLiteralArgument('Invalid Argument', len(arg))

# --------------------
#   Number Arguments
# --------------------


class NumberNode(ArgumentNode, ABC):
	def __init__(self, name):
		super().__init__(name)
		self.min_value = None
		self.max_value = None

	def in_range(self, min_value, max_value):
		self.min_value = min_value
		self.max_value = max_value
		return self

	def _check_in_range(self, value, char_read):
		if (self.min_value is not None and value < self.min_value) or (self.max_value is not None and value > self.max_value):
			raise NumberOutOfRange('Value out of range [{}, {}]'.format(self.min_value, self.max_value), char_read)


class Number(NumberNode):
	"""
	An Integer, or a float
	"""
	def parse(self, text):
		value, read = get_int(text)
		if value is None:
			value, read = get_float(text)
		if value is not None:
			self._check_in_range(value, read)
			return ParseResult(value, read)
		else:
			raise IllegalArgument('Invalid number', read)


class Integer(NumberNode):
	"""
	An Integer
	"""
	def parse(self, text):
		value, read = get_int(text)
		if value is not None:
			self._check_in_range(value, read)
			return ParseResult(value, read)
		else:
			raise IllegalArgument('Invalid integer', read)


class Float(NumberNode):
	def parse(self, text):
		value, read = get_float(text)
		if value is not None:
			self._check_in_range(value, read)
			return ParseResult(value, read)
		else:
			raise IllegalArgument('Invalid float', read)

# ------------------
#   Text Arguments
# ------------------


class TextNode(ArgumentNode, ABC):
	pass


class Text(TextNode):
	"""
	A text argument with no space character
	Just like a single word
	"""
	def parse(self, text):
		arg = get_element(text)
		return ParseResult(arg, len(arg))


class QuotableText(Text):
	QUOTE_CHAR = '"'
	ESCAPE_CHAR = '\\'

	def __init__(self, name):
		super().__init__(name)
		self.empty_allowed = False

	def allow_empty(self):
		self.empty_allowed = True
		return self

	def parse(self, text):
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
					raise IllegalArgument("Illegal usage of escapes", i + 1)
			elif ch == self.ESCAPE_CHAR:
				escaped = True
			elif ch == self.QUOTE_CHAR:
				result = ''.join(collected)
				if not self.empty_allowed and len(result) == 0:
					raise EmptyText('Empty text is not allowed', i + 1)
				return ParseResult(result, i + 1)
			else:
				collected.append(ch)
			i += 1
		raise IllegalArgument("Unclosed quoted string", len(text))


class GreedyText(TextNode):
	"""
	A greedy text argument, which will consume all remaining input
	"""
	def parse(self, text):
		return ParseResult(text, len(text))
