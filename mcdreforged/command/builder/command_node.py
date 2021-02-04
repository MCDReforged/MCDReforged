import collections
import inspect
from abc import ABC
from typing import List, Callable, Iterable, Set, Dict, Type, Any, Union, Optional

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.exception import LiteralNotMatch, NumberOutOfRange, EmptyText, \
	UnknownCommand, UnknownArgument, CommandSyntaxError, UnknownRootArgument, RequirementNotMet, IllegalNodeOperation, \
	CommandError, InvalidNumber, InvalidInteger, InvalidFloat, UnclosedQuotedString, IllegalEscapesUsage, \
	TextLengthOutOfRange
from mcdreforged.command.command_source import CommandSource

SOURCE_CONTEXT_CALLBACK = Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, dict], Any]]
SOURCE_CONTEXT_CALLBACK_BOOL = Union[Callable[[], bool], Callable[[CommandSource], bool], Callable[[CommandSource, dict], bool]]
SOURCE_CONTEXT_CALLBACK_STR = Union[Callable[[], str], Callable[[CommandSource], str], Callable[[CommandSource, dict], str]]
SOURCE_ERROR_CONTEXT_CALLBACK = Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, CommandError], Any], Callable[[CommandSource, CommandError, dict], Any]]


class ParseResult:
	def __init__(self, value: Optional[Any], char_read: int):
		self.value = value
		self.char_read = char_read


class ArgumentNode:
	class ErrorHandler:
		def __init__(self, callback: SOURCE_ERROR_CONTEXT_CALLBACK, handled: bool):
			self.callback = callback
			self.handled = handled

	_ERROR_HANDLER_TYPE = Dict[Type[CommandError], ErrorHandler]

	def __init__(self, name: Optional[str]):
		self.name = name
		self.children_literal = collections.defaultdict(list)  # type: Dict[str, List[Literal]]
		self.children = []  # type: List[ArgumentNode]
		self.callback = None
		self.error_handlers = {}  # type: ArgumentNode._ERROR_HANDLER_TYPE
		self.child_error_handlers = {}  # type: ArgumentNode._ERROR_HANDLER_TYPE
		self.requirement = lambda source: True
		self.requirement_failure_message_getter = None
		self.redirect_node = None

	# --------------
	#   Interfaces
	# --------------

	def then(self, node: 'ArgumentNode') -> 'ArgumentNode':
		"""
		Add a child node to this node
		:param node: a child node for new level command
		"""
		if self.redirect_node is not None:
			raise IllegalNodeOperation('Redirected node is not allowed to add child nodes')
		if isinstance(node, Literal):
			for literal in node.literals:
				self.children_literal[literal].append(node)
		else:
			self.children.append(node)
		return self

	def runs(self, func: SOURCE_CONTEXT_CALLBACK) -> 'ArgumentNode':
		"""
		Executes the given function if the command string ends here
		:param func: A function to execute at this node which accepts maximum 2 parameters (command source and context)
		:rtype: ArgumentNode
		"""
		self.callback = func
		return self

	def requires(self, requirement: SOURCE_CONTEXT_CALLBACK_BOOL, failure_message_getter: Optional[SOURCE_CONTEXT_CALLBACK_STR] = None) -> 'ArgumentNode':
		"""
		Set the requirement for the command source to enter this node
		:param requirement: A callable function which accepts maximum 2 parameters (command source and context)
		and return a bool indicating whether the source is allowed to executes this command or not
		:param failure_message_getter: The reason to show in the exception when the requirement is not met.
		It's a callable function which accepts maximum 2 parameters (command source and context). If it's not specified,
		a default message will be used
		:rtype: ArgumentNode
		"""
		self.requirement = requirement
		self.requirement_failure_message_getter = failure_message_getter
		return self

	def redirects(self, redirect_node: 'ArgumentNode') -> 'ArgumentNode':
		"""
		Redirect the child branches of this node to the child branches of the given node
		:type redirect_node: ArgumentNode
		:rtype: ArgumentNode
		"""
		if self.has_children():
			raise IllegalNodeOperation('Node with children nodes is not allowed to be redirected')
		self.redirect_node = redirect_node
		return self

	def on_error(self, error_type: Type[CommandError], handler: SOURCE_ERROR_CONTEXT_CALLBACK, *, handled: bool = False) -> 'ArgumentNode':
		"""
		When a command error occurs, invoke the handler
		:param error_type: A class that is subclass of CommandError
		:param handler: A callback function which accepts maximum 3 parameters (command source, error and context)
		:param handled: If handled is set to True, error.set_handled() is called automatically when invoking the handler callback
		"""
		if not issubclass(error_type, CommandError):
			raise TypeError('error_type parameter should be a class inherited from CommandError, but class {} found'.format(error_type))
		self.error_handlers[error_type] = self.ErrorHandler(handler, handled)
		return self

	def on_child_error(self, error_type: Type[CommandError], handler: SOURCE_ERROR_CONTEXT_CALLBACK, *, handled: bool = False) -> 'ArgumentNode':
		"""
		When receives a command error from one of the node's child, invoke the handler
		:param error_type: A class that is subclass of CommandError
		:param handler: A callback function which accepts maximum 3 parameters (command source, error and context)
		:param handled: If handled is set to True, error.set_handled() is called automatically when invoking the handler callback
		"""
		if not issubclass(error_type, CommandError):
			raise TypeError('error_type parameter should be a class inherited from CommandError, but class {} found'.format(error_type))
		self.child_error_handlers[error_type] = self.ErrorHandler(handler, handled)
		return self

	# -------------------
	#   Interfaces ends
	# -------------------

	def has_children(self):
		return len(self.children) + len(self.children_literal) > 0

	def parse(self, text: str) -> ParseResult:
		"""
		Try to parse the text and get a argument. Return a ParseResult instance indicating the parsing result
		ParseResult.success: If the parsing is success
		ParseResult.value: The value to store in the context dict
		ParseResult.remaining: The remain
		:param str text: the remaining text to be parsed
		:rtype: ParseResult
		"""
		raise NotImplementedError()

	def __does_store_thing(self):
		"""
		If this argument stores something into the context after parsing the given command string
		For example it might need to store an int after parsing an integer
		In general situation, only Literal Argument doesn't store anything
		:return: bool
		"""
		return self.name is not None

	@staticmethod
	def __smart_callback(callback: Callable, *args):
		sig = inspect.signature(callback)
		spec_args = inspect.getfullargspec(callback).args
		spec_args_len = len(spec_args)
		try:
			sig.bind(*args[:spec_args_len])  # test if using full arg length is ok
		except TypeError:
			if len(spec_args) > 0 and spec_args[0] == 'self':  # hacky fix for class method
				spec_args_len -= 1
			else:
				raise
		return callback(*args[:spec_args_len])

	def __handle_error(self, source, error: CommandError, context: dict, error_handlers: _ERROR_HANDLER_TYPE):
		for error_type, handler in error_handlers.items():
			if isinstance(error, error_type):
				if handler.handled:
					error.set_handled()
				self.__smart_callback(handler.callback, source, error, context)

	def __raise_error(self, source, error: CommandError, context: dict):
		self.__handle_error(source, error, context, self.error_handlers)
		raise error

	def _execute(self, source, command: str, remaining: str, context: dict):
		success_read = len(command) - len(remaining)
		try:
			result = self.parse(remaining)
		except CommandSyntaxError as error:
			error.set_parsed_command(command[:success_read])
			error.set_failed_command(command[:success_read + error.char_read])
			self.__raise_error(source, error, context)
		else:
			success_read += result.char_read
			trimmed_remaining = utils.remove_divider_prefix(remaining[result.char_read:])

			if self.__does_store_thing():
				context[self.name] = result.value

			if self.requirement is not None:
				if not self.__smart_callback(self.requirement, source, context):
					getter = self.requirement_failure_message_getter if self.requirement_failure_message_getter is not None else lambda: None
					failure_message = self.__smart_callback(getter, source, context)
					self.__raise_error(source, RequirementNotMet(command[:success_read], command[:success_read], failure_message), context)

			# Parsing finished
			if len(trimmed_remaining) == 0:
				if self.callback is not None:
					self.__smart_callback(self.callback, source, context)
				else:
					self.__raise_error(source, UnknownCommand(command[:success_read], command[:success_read]), context)
			# Un-parsed command string remains
			else:
				# Redirecting
				node = self if self.redirect_node is None else self.redirect_node

				# No child at all
				if not node.has_children():
					self.__raise_error(source, UnknownArgument(command[:success_read], command), context)

				# Pass the remaining command string to the children
				try:
					# Check literal children first
					next_literal = utils.get_element(trimmed_remaining)
					for child_literal in node.children_literal.get(next_literal, []):
						try:
							child_literal._execute(source, command, trimmed_remaining, context)
							break
						except LiteralNotMatch:
							# it's ok for a direct literal node to fail
							pass
					else:  # All literal children fails
						# No argument child
						if len(node.children) == 0:
							self.__raise_error(source, UnknownArgument(command[:success_read], command), context)
						for child in node.children:
							child._execute(source, command, trimmed_remaining, context)
							break
				except CommandError as error:
					self.__handle_error(source, error, context, self.child_error_handlers)
					raise error from None


class ExecutableNode(ArgumentNode, ABC):
	def execute(self, source, command):
		"""
		Parse and execute this command
		Raise variable CommandError if parsing fails
		:param CommandSource source: the source that executes this command
		:param str command: the command string to execute
		:rtype: None
		"""
		try:
			self._execute(source, command, command, {})
		except LiteralNotMatch as error:
			# the root literal node fails to parse the first element
			raise UnknownRootArgument(error.get_parsed_command(), error.get_failed_command()) from error

# ---------------------------------
#   Argument Node implementations
# ---------------------------------


class Literal(ExecutableNode):
	"""
	A literal argument, doesn't store any value, only for extending and readability of the command
	The only argument type that is allowed to use the execute method
	"""
	def __init__(self, literal: str or Iterable[str]):
		super().__init__(None)
		if isinstance(literal, str):
			literals = {literal}
		elif isinstance(literal, Iterable):
			literals = set(literal)
		else:
			raise TypeError('Only str or Iterable[str] is accepted')
		for literal in literals:
			if not isinstance(literal, str):
				raise TypeError('Literal node only accepts str but {} found'.format(type(literal)))
			if utils.DIVIDER in literal:
				raise TypeError('DIVIDER character "{}" cannot be inside a literal'.format(utils.DIVIDER))
		self.literals = literals  # type: Set[str]

	def parse(self, text):
		arg = utils.get_element(text)
		if arg in self.literals:
			return ParseResult(None, len(arg))
		else:
			raise LiteralNotMatch('Invalid Argument', len(arg))

	def __repr__(self):
		return 'Literal[literals={}]'.format(self.literals)

# --------------------
#   Number Arguments
# --------------------


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

	def _check_in_range_and_return(self, value, char_read):
		if (self.__min_value is not None and value < self.__min_value) or (self.__max_value is not None and value > self.__max_value):
			raise NumberOutOfRange(char_read, value, self.__min_value, self.__max_value)
		return ParseResult(value, char_read)


class Number(NumberNode):
	"""
	An Integer, or a float
	"""
	def parse(self, text):
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
	def parse(self, text):
		value, read = utils.get_int(text)
		if value is not None:
			return self._check_in_range_and_return(value, read)
		else:
			raise InvalidInteger(read)


class Float(NumberNode):
	def parse(self, text):
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

	def _check_length_in_range_and_return(self, text, char_read):
		length = len(text)
		if (self.__min_length is not None and length < self.__min_length) or (self.__max_length is not None and length > self.__max_length):
			raise TextLengthOutOfRange(char_read, length, self.__min_length, self.__max_length)
		return ParseResult(text, char_read)


class Text(TextNode):
	"""
	A text argument with no space character
	Just like a single word
	"""
	def parse(self, text):
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
		raise UnclosedQuotedString(len(text))


class GreedyText(TextNode):
	"""
	A greedy text argument, which will consume all remaining input
	"""
	def parse(self, text):
		return self._check_length_in_range_and_return(text, len(text))
