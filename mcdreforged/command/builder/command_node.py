import collections
import inspect
from abc import ABC
from typing import List, Callable, Iterable, Set, Dict, Type, Any, Union

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.exception import LiteralNotMatch, NumberOutOfRange, IllegalArgument, EmptyText, \
	UnknownCommand, UnknownArgument, CommandSyntaxError, UnknownRootArgument, RequirementNotMet, IllegalNodeOperation, \
	CommandError
from mcdreforged.command.command_source import CommandSource

ParseResult = collections.namedtuple('ParseResult', 'value char_read')


class ArgumentNode:
	def __init__(self, name):
		self.name = name
		self.children_literal = {}  # type: Dict[str, List[Literal]]
		self.children = []  # type: List[ArgumentNode]
		self.callback = None
		self.error_listeners = {}  # type: Dict[Type[CommandError], Callable[[CommandSource, CommandError], Any]]
		self.requirement = lambda source: True
		self.redirect_node = None

	# --------------
	#   Interfaces
	# --------------

	def then(self, node):
		"""
		Add a child node to this node
		:param ArgumentNode node: a child node for new level command
		:rtype: ArgumentNode
		"""
		if self.redirect_node is not None:
			raise IllegalNodeOperation('Redirected node is not allowed to add child nodes')
		if isinstance(node, Literal):
			for literal in node.literals:
				nodes = self.children_literal.get(literal, [])
				nodes.append(node)
				self.children_literal[literal] = nodes
		else:
			self.children.append(node)
		return self

	def runs(self, func: Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, dict], Any]]):
		"""
		Executes the given function if the command string ends here
		:param func: A function to execute at this node, with 0 to 2 args
		:rtype: ArgumentNode
		"""
		self.callback = func
		return self

	def requires(self, requirement: Union[Callable[[], bool], Callable[[CommandSource], bool]]):
		"""
		Set the requirement for the command source to enter this node
		:param requirement: A callable function which accepts 1 parameter (the command source) and return a bool
		indicating whether the source is allowed to executes this command or not
		:rtype: ArgumentNode
		"""
		self.requirement = requirement
		return self

	def redirects(self, redirect_node):
		"""
		Redirect the child branches of this node to the child branches of the given node
		:type redirect_node: ArgumentNode
		:rtype: ArgumentNode
		"""
		if self.has_children():
			raise IllegalNodeOperation('Node with children nodes is not allowed to be redirected')
		self.redirect_node = redirect_node
		return self

	def on_error(self, error_type: Type[CommandError], listener: Union[Callable[[], Any], Callable[[CommandSource], Any], Callable[[CommandSource, CommandError], Any], Callable[[CommandSource, CommandError, dict], Any]]):
		"""
		When a command error occurs, invoke the listener
		:param error_type: A class of CommandError or inherited from CommandError
		:param listener: A callback function, with 0 to 3 args
		:return:
		"""
		self.error_listeners[error_type] = listener
		return self

	# -------------------
	#   Interfaces ends
	# -------------------

	def has_children(self):
		return len(self.children) + len(self.children_literal) > 0

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
		def run(sal: int):
			arg_len = min(sal, len(args))
			return callback(*args[:arg_len])

		spec_args = inspect.getfullargspec(callback).args
		spec_args_len = len(spec_args)
		try:
			return run(spec_args_len)
		except TypeError as e:
			error = e
		if len(spec_args) > 0 and spec_args[0] == 'self':  # hacky fix for class method
			return run(spec_args_len - 1)
		else:
			raise error

	def __raise_error(self, source, error: CommandError, context: dict):
		listener = self.error_listeners.get(type(error))
		if listener is not None:
			self.__smart_callback(listener, source, error, context)
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

			if self.requirement is not None:
				if not self.__smart_callback(self.requirement, source):
					self.__raise_error(source, RequirementNotMet(command[:success_read], command[:success_read]), context)

			if self.__does_store_thing():
				context[self.name] = result.value

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
			raise UnknownRootArgument(error.get_parsed_command(), error.get_failed_command())

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
		self.min_value = None
		self.max_value = None

	def at_min(self, min_value):
		"""
		Static range check
		"""
		self.min_value = min_value
		return self

	def at_max(self, max_value):
		"""
		Static range check
		"""
		self.max_value = max_value
		return self

	def in_range(self, min_value, max_value):
		"""
		Static range check
		"""
		self.at_min(min_value)
		self.at_max(max_value)
		return self

	def _check_in_range(self, value, char_read):
		if (self.min_value is not None and value < self.min_value) or (self.max_value is not None and value > self.max_value):
			raise NumberOutOfRange('Value out of range [{}, {}]'.format(self.min_value, self.max_value), char_read)


class Number(NumberNode):
	"""
	An Integer, or a float
	"""
	def parse(self, text):
		value, read = utils.get_int(text)
		if value is None:
			value, read = utils.get_float(text)
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
		value, read = utils.get_int(text)
		if value is not None:
			self._check_in_range(value, read)
			return ParseResult(value, read)
		else:
			raise IllegalArgument('Invalid integer', read)


class Float(NumberNode):
	def parse(self, text):
		value, read = utils.get_float(text)
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
		arg = utils.get_element(text)
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
