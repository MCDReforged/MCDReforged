import collections
import inspect
from abc import ABC
from contextlib import contextmanager
from types import MethodType
from typing import List, Callable, Iterable, Set, Dict, Type, Any, Union, Optional, Collection

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.exception import LiteralNotMatch, NumberOutOfRange, EmptyText, \
	UnknownCommand, UnknownArgument, CommandSyntaxError, UnknownRootArgument, RequirementNotMet, IllegalNodeOperation, \
	CommandError, InvalidNumber, InvalidInteger, InvalidFloat, UnclosedQuotedString, IllegalEscapesUsage, \
	TextLengthOutOfRange
from mcdreforged.command.command_source import CommandSource

SOURCE_CONTEXT_CALLBACK = Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, dict], Any]]
SOURCE_CONTEXT_CALLBACK_BOOL = Union[Callable[[], bool], Callable[[CommandSource], bool], Callable[[CommandSource, dict], bool]]
SOURCE_CONTEXT_CALLBACK_STR = Union[Callable[[], str], Callable[[CommandSource], str], Callable[[CommandSource, dict], str]]
SOURCE_CONTEXT_CALLBACK_STR_LIST = Union[Callable[[], List[str]], Callable[[CommandSource], List[str]], Callable[[CommandSource, dict], List[str]]]
SOURCE_ERROR_CONTEXT_CALLBACK = Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, CommandError], Any], Callable[[CommandSource, CommandError, dict], Any]]


class ParseResult:
	def __init__(self, value: Optional[Any], char_read: int):
		self.value = value
		self.char_read = char_read


class CommandContext(dict):
	def __init__(self, source, command: str):
		super().__init__()
		self.source = source
		self.command = command
		self.cursor = 0
		self.node_path = []  # type: List[ArgumentNode]

	@property
	def command_read(self):
		return self.command[:self.cursor]

	@property
	def command_remaining(self):
		return self.command[self.cursor:]

	@contextmanager
	def enter_child(self, new_cursor: int, node: 'ArgumentNode'):
		prev_cursor = self.cursor
		self.cursor = new_cursor
		self.node_path.append(node)
		try:
			yield
		finally:
			self.cursor = prev_cursor
			self.node_path.pop(len(self.node_path) - 1)
			self.pop(node.name, None)


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
		self.suggestion_getter = lambda: []

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

	def suggests(self, suggestion: SOURCE_CONTEXT_CALLBACK_STR_LIST):
		self.suggestion_getter = suggestion

	def suggests_matching(self, keywords: Collection[str]):
		def suggest(source, context: CommandContext):
			return [keyword for keyword in keywords if keyword.startswith(context.command_remaining)]
		self.suggests(suggest)

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
		if isinstance(callback, MethodType):  # class method, remove the 1st param
			spec_args_len -= 1
		try:
			sig.bind(*args[:spec_args_len])  # test if using full arg length is ok
		except TypeError:
			raise
		return callback(*args[:spec_args_len])

	def __handle_error(self, error: CommandError, context: CommandContext, error_handlers: _ERROR_HANDLER_TYPE):
		for error_type, handler in error_handlers.items():
			if isinstance(error, error_type):
				if handler.handled:
					error.set_handled()
				self.__smart_callback(handler.callback, context.source, error, context)

	def __raise_error(self, error: CommandError, context: CommandContext):
		self.__handle_error(error, context, self.error_handlers)
		raise error

	def _get_suggestions(self, context: CommandContext) -> List[str]:
		return self.__smart_callback(self.suggestion_getter, context.source, context)

	def _execute_command(self, context: CommandContext) -> None:
		command = context.command  # type: str
		try:
			result = self.parse(context.command_remaining)
		except CommandSyntaxError as error:
			error.set_parsed_command(context.command_read)
			error.set_failed_command(context.command_read + context.command_remaining[error.char_read:])
			self.__raise_error(error, context)
		else:
			next_remaining = utils.remove_divider_prefix(context.command_remaining[result.char_read:])  # type: str
			total_read = len(command) - len(next_remaining)  # type: int

			if self.__does_store_thing():
				context[self.name] = result.value

			if self.requirement is not None:
				if not self.__smart_callback(self.requirement, context.source, context):
					getter = self.requirement_failure_message_getter or (lambda: None)
					failure_message = self.__smart_callback(getter, context.source, context)
					self.__raise_error(RequirementNotMet(context.command_read, context.command_read, failure_message), context)

			# Parsing finished
			if len(next_remaining) == 0:
				if self.callback is not None:
					self.__smart_callback(self.callback, context.source, context)
				else:
					self.__raise_error(UnknownCommand(context.command_read, context.command_read), context)
			# Un-parsed command string remains
			else:
				# Redirecting
				node = self if self.redirect_node is None else self.redirect_node

				argument_unknown = False
				# No child at all
				if not node.has_children():
					argument_unknown = True
				else:
					# Pass the remaining command string to the children
					next_literal = utils.get_element(next_remaining)
					try:
						# Check literal children first
						literal_error = None
						for child_literal in node.children_literal.get(next_literal, []):
							try:
								with context.enter_child(total_read, child_literal):
									child_literal._execute_command(context)
								break
							except CommandError as e:
								# it's ok for a direct literal node to fail
								# other literal might still have a chance to consume this command
								literal_error = e
						else:  # All literal children fails
							if literal_error is not None:
								raise literal_error
							for child in node.children:
								with context.enter_child(total_read, child):
									child._execute_command(context)
								break
							else:  # No argument child
								argument_unknown = True

					except CommandError as error:
						self.__handle_error(error, context, self.child_error_handlers)
						raise error from None

				if argument_unknown:
					self.__raise_error(UnknownArgument(context.command_read, command), context)

	def _generate_suggestions(self, context: CommandContext) -> List[str]:
		suggestions = []  # type: List[str]
		try:
			result = self.parse(context.command_remaining)
		except CommandSyntaxError:
			return [context.command_read + s for s in self._get_suggestions(context)]
		else:
			success_read = len(context.command) - len(context.command_remaining) + result.char_read  # type: int
			next_remaining = utils.remove_divider_prefix(context.command_remaining[result.char_read:])  # type: str
			total_read = len(context.command) - len(next_remaining)  # type: int

			if self.__does_store_thing():
				context[self.name] = result.value

			if self.requirement is not None and not self.__smart_callback(self.requirement, context.source, context):
				return []

			# Parsing finished
			if len(next_remaining) == 0:
				# total_read == success_read means DIVIDER does not exists at the end of the input string
				# in that case, don't give any suggestions
				if success_read == total_read:
					return []

			node = self if self.redirect_node is None else self.redirect_node
			# Check literal children first
			for child_literal in node.children_literal.get(utils.get_element(next_remaining), []):
				with context.enter_child(total_read, child_literal):
					suggestions.extend(child_literal._generate_suggestions(context))
			else:  # All literal children fails
				for literal_list in node.children_literal.values():
					for child_literal in literal_list:
						with context.enter_child(total_read, child_literal):
							suggestions.extend(child_literal._generate_suggestions(context))
				for child in node.children:
					with context.enter_child(total_read, child):
						suggestions.extend(child._generate_suggestions(context))

		return suggestions


class EntryNode(ArgumentNode, ABC):
	def execute(self, source, command):
		"""
		Parse and execute this command
		Raise variable CommandError if parsing fails
		:param CommandSource source: the source that executes this command
		:param str command: the command string to execute
		"""
		try:
			self._execute_command(CommandContext(source, command))
		except LiteralNotMatch as error:
			# the root literal node fails to parse the first element
			raise UnknownRootArgument(error.get_parsed_command(), error.get_failed_command()) from error

	def generate_suggestions(self, source, command) -> List[str]:
		"""
		Get a list of command suggestion of given command
		Return an empty list if parsing fails
		:param CommandSource source: the source that executes this command
		:param str command: the command string to execute
		"""
		return self._generate_suggestions(CommandContext(source, command))

# ---------------------------------
#   Argument Node implementations
# ---------------------------------


class Literal(EntryNode):
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
		self.suggests_matching(self.literals)

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
