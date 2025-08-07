import collections
from abc import ABC, abstractmethod
from typing import List, Callable, Iterable, Set, Dict, Type, Any, Union, Optional, NamedTuple, TypedDict, TypeVar

from typing_extensions import Self, override, NotRequired

from mcdreforged.command.builder import command_builder_utils as utils
from mcdreforged.command.builder.callback import CallbackError, ScheduledCallback, DirectCallbackInvoker
from mcdreforged.command.builder.common import ParseResult, CommandContext, CommandSuggestions, CommandSuggestion, CommandExecutions, CommandExecution
from mcdreforged.command.builder.exception import LiteralNotMatch, UnknownCommand, UnknownArgument, CommandSyntaxError, \
	UnknownRootArgument, RequirementNotMet, IllegalNodeOperation, \
	CommandError
from mcdreforged.command.command_source import CommandSource
from mcdreforged.utils import tree_printer, class_utils, collection_utils
from mcdreforged.utils.types.message import MessageText

_T = TypeVar('_T')
__SOURCE_CONTEXT_CALLBACK = Union[
	Callable[[], Any],
	Callable[[CommandSource], Any],
	Callable[[CommandSource, CommandContext], Any]
]
__SOURCE_CONTEXT_CALLBACK_BOOL = Union[
	Callable[[], bool],
	Callable[[CommandSource], bool],
	Callable[[CommandSource, CommandContext], bool]
]
__SOURCE_CONTEXT_CALLBACK_MSG = Union[
	Callable[[], MessageText],
	Callable[[CommandSource], MessageText],
	Callable[[CommandSource, CommandContext], MessageText]
]
__SOURCE_CONTEXT_CALLBACK_STR_ITERABLE = Union[
	Callable[[], Iterable[str]],
	Callable[[CommandSource], Iterable[str]],
	Callable[[CommandSource, CommandContext], Iterable[str]]
]
__SOURCE_ERROR_CONTEXT_CALLBACK = Union[
	Callable[[], Any],
	Callable[[CommandSource], Any],
	Callable[[CommandSource, CommandError], Any],
	Callable[[CommandSource, CommandError, CommandContext], Any]
]

RUNS_CALLBACK = __SOURCE_CONTEXT_CALLBACK
ERROR_HANDLER_CALLBACK = __SOURCE_ERROR_CONTEXT_CALLBACK
FAIL_MSG_CALLBACK = __SOURCE_CONTEXT_CALLBACK_MSG
SUGGESTS_CALLBACK = __SOURCE_CONTEXT_CALLBACK_STR_ITERABLE
REQUIRES_CALLBACK = __SOURCE_CONTEXT_CALLBACK_BOOL
PRECONDITION_CALLBACK = __SOURCE_CONTEXT_CALLBACK_BOOL


class _ErrorHandler(NamedTuple):
	callback: ERROR_HANDLER_CALLBACK
	handled: bool


class _Requirement(NamedTuple):
	requirement: REQUIRES_CALLBACK
	failure_message_getter: Optional[FAIL_MSG_CALLBACK]


_ERROR_HANDLER_TYPE = Dict[Type[CommandError], _ErrorHandler]


class AbstractNode(ABC):
	"""
	:class:`AbstractNode` is base class of all command nodes. It's also an abstract class.
	It provides several methods for building up the command tree
	"""

	def __init__(self):
		self._children_literal: Dict[str, List[Literal]] = collections.defaultdict(list)  # mapping from literal text to related Literal nodes
		self._children: List[AbstractNode] = []
		self._callback: Optional[RUNS_CALLBACK] = None
		self._error_handlers: _ERROR_HANDLER_TYPE = {}
		self._child_error_handlers: _ERROR_HANDLER_TYPE = {}
		self._preconditions: List[PRECONDITION_CALLBACK] = []
		self._requirements: List[_Requirement] = []
		self._redirect_node: Optional[AbstractNode] = None
		self._suggestion_getter: SUGGESTS_CALLBACK = lambda: []

	# --------------
	#   Interfaces
	# --------------

	def then(self, node: 'AbstractNode') -> Self:
		"""
		Attach a child node to its children list, and then return itself

		It's used for building the command tree structure

		:param node: A node instance to be added to current node's children list

		Example::

			Literal('!!email'). \\
			then(Literal('list')). \\
			then(Literal('remove'). \\
				then(Integer('email_id'))
			). \\
			then(Literal('send'). \\
				then(Text('player'). \\
					then(GreedyText('message'))
				)
			)
		"""
		if self._redirect_node is not None:
			raise IllegalNodeOperation('Redirected node is not allowed to add child nodes')
		class_utils.check_type(node, AbstractNode)
		if isinstance(node, Literal):
			for literal in node.literals:
				self._children_literal[literal].append(node)
		else:
			self._children.append(node)
		return self

	def runs(self, func: RUNS_CALLBACK) -> Self:
		"""
		Set the callback function of this node. When the command parsing finished at this node, the callback function will be executed

		The callback function is allowed to accept 0 to 2 arguments
		(a :class:`~mcdreforged.command.command_source.CommandSource` as command source
		and a :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`) as context).
		For example, the following 4 functions are available callbacks::

			def callback1():
				pass

			def callback2(source: CommandSource):
				pass

			def callback3(source: CommandSource, context: dict):
				pass

			callback4 = lambda src: src.reply('pong')
			node1.runs(callback1)
			node2.runs(callback2)
			node3.runs(callback3)
			node4.runs(callback4)

		Both of them can be used as the argument of the ``runs`` method

		This dynamic callback argument adaptation is used in all callback invoking of the command nodes

		:param func: A callable that accepts up to 2 arguments.
			Argument list: :class:`~mcdreforged.command.command_source.CommandSource`, :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)
		"""
		class_utils.check_type(func, Callable)
		self._callback = func
		return self

	def requires(self, requirement: REQUIRES_CALLBACK, failure_message_getter: Optional[FAIL_MSG_CALLBACK] = None) -> Self:
		"""
		Set the requirement tester callback of the node. When entering this node, MCDR will invoke the requirement tester
		to see if the current command source and context meet the specified condition

		If the tester callback return True, nothing will happen, MCDR will continue parsing the rest of the command

		If the tester callback return False, a ``RequirementNotMet`` exception will be risen.
		At this time if the *failure_message_getter* parameter is available, MCDR will invoke *failure_message_getter* to get the message string
		of the ``RequirementNotMet`` exception, otherwise a default message will be used

		.. versionadded:: v2.7.0
			Multiple :meth:`requires` call results in an "and" combination of all given requirements,
			i.e. the current command context is satisfied iif. all given requirements are satisfied

		:param requirement: A callable that accepts up to 2 arguments and returns a bool.
			Argument list: :class:`~mcdreforged.command.command_source.CommandSource`, :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)
		:param failure_message_getter: An optional callable that accepts up to 2 arguments and returns a str or a :class:`~mcdreforged.minecraft.rtext.text.RTextBase`.
			Argument list: :class:`~mcdreforged.command.command_source.CommandSource`, :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)

		Example usages::

			node1.requires(lambda src: src.has_permission(3))  # Permission check, error if the permission is not enough
			node2.requires(lambda src, ctx: ctx['page_count'] <= get_max_page())  # Dynamic range check
			node3.requires(lambda src, ctx: is_legal(ctx['target']), lambda src, ctx: 'target {} is illegal'.format(ctx['target']))  # Customized failure message
		"""
		class_utils.check_type(requirement, Callable)
		class_utils.check_type(failure_message_getter, [Callable, None])
		self._requirements.append(_Requirement(requirement, failure_message_getter))
		return self

	def precondition(self, precondition: PRECONDITION_CALLBACK) -> Self:
		"""
		Set the precondition callback for this node. Before attempting to enter this node, MCDR will invoke the precondition callback
		to see if the current command source and context meet the specified condition

		If the precondition callback returns True, the node will remain accessible, and MCDR will continue entering the node

		If the precondition callback returns False, the node will be filtered out and treated as if it does not exist

		.. versionadded:: v2.14.0

		:param precondition: A callable that accepts up to 2 arguments and returns a bool.
			Argument list: :class:`~mcdreforged.command.command_source.CommandSource`, :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)

		Example usages::

			node1.precondition(lambda src: src.has_permission(3))  # Permission check, but hide if the permission is not enough
			node2.precondition(lambda src, ctx: 'foo' in ctx)  # Avoid re-assigning the "foo" argument
		"""
		class_utils.check_type(precondition, Callable)
		self._preconditions.append(precondition)
		return self

	def redirects(self, redirect_node: 'AbstractNode') -> Self:
		"""
		Redirect all further child nodes command parsing to another given node

		Redirected stuffs:

		* Children node traversal
		* Command callback, if current node doesn't have a callback

		Unredirected stuffs:

		* Command parsing, i.e. parsing the literal / argument value of the node from command
		* Requirement testing
		* Precondition testing
		* Suggestion fetching

		Example use cases:

		* You want a short command and full-path command that will all execute the same commands
		* You want to repeatedly re-enter a command node's children when parsing commands

		Pay attention to the difference between :meth:`redirects` and :meth:`then`. :meth:`redirects` is to redirect the child nodes,
		and :meth:`then` is to add a child node

		:param redirect_node: A node instance which current node is redirecting to
		"""
		if self.has_children():
			raise IllegalNodeOperation('Node with children nodes is not allowed to be redirected')
		class_utils.check_type(redirect_node, AbstractNode)
		self._redirect_node = redirect_node
		return self

	def suggests(self, suggestion: SUGGESTS_CALLBACK) -> Self:
		"""
		Set the provider for command suggestions of this node

		:class:`Literal` node does not support this method

		Examples::

			Literal('!!whereis'). \\
				then(
					Text('player_name').
					suggests(lambda: ['Steve', 'Alex']).
					runs(lambda src, ctx: find_player(src, ctx['player_name']))
				)

		When the user input ``!!whereis`` in the console and a space character, MCDR will show the suggestions ``"Steve"`` and ``"Alex"``

		:param suggestion: A callable function which accepts up to 2 parameters and return an iterable of str indicating the current command suggestions.
			Argument list: :class:`~mcdreforged.command.command_source.CommandSource`, :class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)
		"""
		class_utils.check_type(suggestion, Callable)
		self._suggestion_getter = suggestion
		return self

	def on_error(self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		"""
		When a command error occurs, the given will invoke the given handler to handle with the error

		:param error_type: A class that is subclass of :class:`CommandError`
		:param handler: A callable that accepts up to 3 arguments.
			Argument list: :class:`~mcdreforged.command.builder.exception.CommandError`, :class:`~mcdreforged.command.command_source.CommandSource`,
			:class:`dict` (:class:`~mcdreforged.command.builder.common.CommandContext`)
		:keyword handled: If handled is set to True, :meth:`CommandError.set_handled<mcdreforged.command.builder.exception.CommandError.set_handled>`
			is called automatically when invoking the handler callback
		"""
		if not issubclass(error_type, CommandError):
			raise TypeError('error_type parameter should be a class inherited from CommandError, but class {} found'.format(error_type))
		class_utils.check_type(error_type, type)
		class_utils.check_type(handler, Callable)
		self._error_handlers[error_type] = _ErrorHandler(handler, handled)
		return self

	def on_child_error(self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		"""
		Similar to :meth:`on_error`, but it gets triggered only when the node receives a command error from one of the node's direct or indirect child
		"""
		if not issubclass(error_type, CommandError):
			raise TypeError('error_type parameter should be a class inherited from CommandError, but class {} found'.format(error_type))
		class_utils.check_type(error_type, type)
		class_utils.check_type(handler, Callable)
		self._child_error_handlers[error_type] = _ErrorHandler(handler, handled)
		return self

	def print_tree(self, line_writer: tree_printer.LineWriter = print):
		"""
		Print the command tree in a read-able format. Mostly used in debugging

		:param line_writer: A printer function that accepts a str

		.. versionadded:: v2.6.0
		"""
		def children_getter(node: AbstractNode) -> List[AbstractNode]:
			return node.get_children()
		tree_printer.print_tree(self, children_getter, str, line_writer)

	# -------------------
	#   Interfaces ends
	# -------------------

	@abstractmethod
	def _get_usage(self) -> str:
		raise NotImplementedError()

	def has_children(self):
		return len(self._children) + len(self._children_literal) > 0

	def get_children(self) -> List['AbstractNode']:
		children = []
		for literal_list in self._children_literal.values():
			children.extend(literal_list)
		children.extend(self._children)
		return collection_utils.unique_list(children)

	def _on_visited(self, context: CommandContext, parsed_result: ParseResult):
		"""
		Invoked when this node is visited, right after the node successfully parses a command segment

		A node can use the context dict to store its provided value here
		"""
		pass

	@abstractmethod
	def parse(self, text: str) -> ParseResult:
		"""
		Try to parse the text and get an argument

		* ``ParseResult.value``: The value to store in the context dict
		* ``ParseResult.remaining``: The remaining unparsed text

		:param text: the text to be parsed. It's supposed to not be started with DIVIDER character
		:meta private:
		"""
		raise NotImplementedError()

	@staticmethod
	def __smart_callback(callback: Callable, args: tuple, callback_error_factory: CallbackError.Builder):
		# make sure all passed CommandContext are copies
		adjusted_args = tuple(
			arg.copy() if isinstance(arg, CommandContext) else arg
			for arg in args
		)
		return ScheduledCallback(callback, adjusted_args, callback_error_factory).invoke(DirectCallbackInvoker())

	def __handle_error(self, error: CommandError, context: CommandContext, error_handlers: _ERROR_HANDLER_TYPE):
		for error_type, handler in error_handlers.items():
			if isinstance(error, error_type):
				self.__smart_callback(handler.callback, (context.source, error, context), CallbackError.builder(context, 'error handling'))
				if handler.handled:
					error.set_handled()

	def __raise_error(self, error: CommandError, context: CommandContext):
		self.__handle_error(error, context, self._error_handlers)
		raise error

	def __check_requirements(self, context: CommandContext) -> Optional[_Requirement]:
		"""
		:return: None: requirement check passed; otherwise, the unsatisfied requirement
		"""
		for req in self._requirements:
			ok = self.__smart_callback(req.requirement, (context.source, context), CallbackError.builder(context, 'requirements check'))
			if not ok:
				return req
		return None

	def __check_preconditions(self, context: CommandContext) -> bool:
		for precondition in self._preconditions:
			ok = self.__smart_callback(precondition, (context.source, context), CallbackError.builder(context, 'preconditions check'))
			if not ok:
				return False
		return True

	def _get_suggestions(self, context: CommandContext) -> Iterable[str]:
		return self.__smart_callback(self._suggestion_getter, (context.source, context), CallbackError.builder(context, 'suggestions getting'))

	def _execute_command(self, context: CommandContext) -> CommandExecutions:
		command = context.command
		executions = CommandExecutions()
		try:
			parse_result = self.parse(context.command_remaining)
		except CommandSyntaxError as error:
			error.set_parsed_command(context.command_read)
			error.set_failed_command(context.command_read + context.command_remaining[:error.char_read])
			self.__raise_error(error, context)
		else:
			next_remaining = utils.remove_divider_prefix(context.command_remaining[parse_result.char_read:])
			total_read = len(command) - len(next_remaining)

			with context.visit_node(self, parse_result, total_read):
				req = self.__check_requirements(context)
				if req is not None:  # requirement check failed
					if req.failure_message_getter is not None:
						failure_message = self.__smart_callback(req.failure_message_getter, (context.source, context), CallbackError.builder(context, 'failure message getting'))
					else:
						failure_message = None
					self.__raise_error(RequirementNotMet(context.command_read, context.command_read, failure_message), context)

				# Parsing finished
				if len(next_remaining) == 0:
					callback = self._callback
					if callback is None and self._redirect_node is not None:
						callback = self._redirect_node._callback
					if callback is not None:
						context2 = context.copy()
						executions.append(CommandExecution(
							context=context2,
							scheduled_callback=ScheduledCallback(callback, (context2.source, context2), CallbackError.builder(context2, 'command callback')),
						))
					else:
						self.__raise_error(UnknownCommand(context.command_read, context.command_read), context)
				# Un-parsed command string remains
				else:
					# Redirecting
					node = self if self._redirect_node is None else self._redirect_node

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
							child_literal: AbstractNode  # satisfy pycharm's static checker on the __check_preconditions() call
							for child_literal in node._children_literal.get(next_literal, []):
								if not child_literal.__check_preconditions(context):
									continue
								try:
									with context.enter_child(child_literal):
										executions.extend(child_literal._execute_command(context))
									break
								except CommandError as e:
									# it's ok for a direct literal node to fail
									# other literal might still have a chance to consume this command
									literal_error = e
							else:  # All literal children fails
								if literal_error is not None:
									raise literal_error
								for child in node._children:
									if not child.__check_preconditions(context):
										continue
									try:
										with context.enter_child(child):
											executions.extend(child._execute_command(context))
									except UnknownArgument:
										continue
									break
								else:  # No argument child
									argument_unknown = True

						except CommandError as error:
							self.__handle_error(error, context, self._child_error_handlers)
							raise error from None

					if argument_unknown:
						self.__raise_error(UnknownArgument(context.command_read, command), context)

		return executions

	def _generate_suggestions(self, context: CommandContext) -> CommandSuggestions:
		"""
		Return a list of tuple (suggested command, suggested argument)
		"""
		def self_suggestions():
			return CommandSuggestions([CommandSuggestion(command_read_at_the_beginning, s) for s in self._get_suggestions(context)])

		suggestions = CommandSuggestions()
		# [!!aa bb cc] dd
		# read         suggested
		command_read_at_the_beginning = context.command_read
		if len(context.command_remaining) == 0:
			return self_suggestions()
		try:
			result = self.parse(context.command_remaining)
		except CommandSyntaxError:
			return self_suggestions()
		else:
			success_read = len(context.command) - len(context.command_remaining) + result.char_read
			next_remaining = utils.remove_divider_prefix(context.command_remaining[result.char_read:])
			total_read = len(context.command) - len(next_remaining)

			with context.visit_node(self, result, total_read):
				if self.__check_requirements(context) is not None:
					return CommandSuggestions()

				# Parsing finished
				if len(next_remaining) == 0:
					# total_read == success_read means DIVIDER does not exist at the end of the input string
					# in that case, ends at this current node
					if success_read == total_read:
						return self_suggestions()

				node = self if self._redirect_node is None else self._redirect_node
				# Check literal children first
				children_literal = node._children_literal.get(utils.get_element(next_remaining), [])
				child_literal: AbstractNode  # satisfy pycharm's static checker on the __check_preconditions() call
				for child_literal in children_literal:
					if not child_literal.__check_preconditions(context):
						continue
					with context.enter_child(child_literal):
						suggestions.extend(child_literal._generate_suggestions(context))
				if len(children_literal) == 0:
					for literal_list in node._children_literal.values():
						for child_literal in literal_list:
							if not child_literal.__check_preconditions(context):
								continue
							with context.enter_child(child_literal):
								suggestions.extend(child_literal._generate_suggestions(context))
					usages = []
					for child in node._children:
						if not child.__check_preconditions(context):
							continue
						with context.enter_child(child):
							suggestions.extend(child._generate_suggestions(context))
							if len(next_remaining) == 0:
								usages.append(child._get_usage())
					if len(next_remaining) == 0:
						suggestions.complete_hint = '|'.join(usages)
		return suggestions


class EntryNode(AbstractNode, ABC):
	def _entry_execute(self, source: CommandSource, command: str) -> CommandExecutions:
		"""
		Parse and execute this command

		:param source: the source that executes this command
		:param command: the command string to execute
		:raise CommandError: if parsing fails
		:meta private:
		"""
		try:
			context = CommandContext(source, command)
			with context.enter_child(self):
				return self._execute_command(context)
		except LiteralNotMatch as error:
			# the root literal node fails to parse the first element
			raise UnknownRootArgument(error.get_parsed_command(), error.get_failed_command()) from error

	def _entry_generate_suggestions(self, source: CommandSource, command: str) -> CommandSuggestions:
		"""
		Get a list of command suggestion of given command

		Return an empty list if parsing fails

		:param source: the source that executes this command
		:param command: the command string to execute
		:meta private:
		"""
		context = CommandContext(source, command)
		with context.enter_child(self):
			return self._generate_suggestions(context)


class Literal(EntryNode):
	"""
	Literal node is a special node. It doesn't output any value. It's more like a command branch carrier

	Literal node can accept a str as its literal in its constructor. A literal node accepts the parsing command only when the next element of the parsing command exactly matches the literal of the node

	Literal node is the only node that can start a command execution
	"""
	def __init__(self, literal: str or Iterable[str]):
		super().__init__()
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
		self.literals: Set[str] = literals
		self._suggestion_getter = lambda: self.literals

	@override
	def _get_usage(self) -> str:
		return '|'.join(sorted(self.literals))

	@override
	def suggests(self, suggestion: SUGGESTS_CALLBACK) -> 'AbstractNode':
		raise IllegalNodeOperation('Literal node does not support suggests')

	@override
	def parse(self, text):
		arg = utils.get_element(text)
		if arg in self.literals:
			return ParseResult(None, len(arg))
		else:
			raise LiteralNotMatch('Invalid Argument', len(arg))

	def __str__(self):
		return 'Literal {}'.format(repr(tuple(self.literals)[0]) if len(self.literals) == 1 else set(self.literals))

	def __repr__(self):
		return class_utils.represent(self, {'literals': self.literals})


class ArgumentNode(AbstractNode, ABC):
	"""
	Argument node is an abstract base class for all nodes which store parsed values

	It has a str field ``name`` which is used as the key used in storing parsed value in context
	"""

	class _InitKwargs(TypedDict):
		accumulate: NotRequired[bool]
		metavar: NotRequired[str]

	def __init__(
			self, name: str, *,
			accumulate: Optional[bool] = None,
			metavar: Optional[str] = None,
	):
		"""
		:param name: The name of the argument node. Should be unique within the command tree path
		:keyword accumulate: If set to True, then the parsed value will be stored in a list in the command context.
			Re-visiting of this node appends new value to the end of the list
		:keyword metavar: Optional str. It behaves like the *metavar* kwarg of :external:meth:`argparse.ArgumentParser.add_argument`,
			which overrides the name displayed of the command suggestion usage placeholder.
			If not provided, the *name* argument will be used as the default placeholder

		.. versionadded:: v2.13.0
			The *accumulate* parameter
		.. versionadded:: v2.14.0
			The *metavar* parameter
		"""
		super().__init__()
		self.__name = name
		self.__accumulate: bool = bool(accumulate)
		self.__metavar = metavar

	@override
	def _on_visited(self, context: CommandContext, parsed_result: ParseResult):
		if self.__accumulate:
			if self.__name not in context:
				context[self.__name] = []
			context[self.__name].append(parsed_result.value)
		else:
			context[self.__name] = parsed_result.value

	def get_name(self) -> str:
		return self.__name

	@override
	def _get_usage(self) -> str:
		return '<{}>'.format(self.__metavar or self.__name)

	def __str__(self):
		return '{} <{}>'.format(self.__class__.__name__, self.get_name())

	def __repr__(self):
		fields = {'name': self.__name}
		if self.__accumulate:
			fields['accumulate'] = True
		if self.__metavar:
			fields['metavar'] = True
		return class_utils.represent(self, fields)
