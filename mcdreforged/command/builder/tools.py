from abc import ABC
from typing import Dict, Callable, TYPE_CHECKING, Optional, List, TypeVar, Generic, Any, Type

from mcdreforged.command.builder.exception import CommandError
from mcdreforged.command.builder.nodes.basic import RUNS_CALLBACK, Literal, AbstractNode, ArgumentNode, REQUIRES_CALLBACK, FAIL_MSG_CALLBACK, SUGGESTS_CALLBACK, ERROR_HANDLER_CALLBACK
from mcdreforged.command.command_source import CommandSource
from mcdreforged.utils import tree_printer

if TYPE_CHECKING:
	from mcdreforged.plugin.server_interface import PluginServerInterface


class Requirements:
	"""
	A common callback function factory for command node requirement testing

	Example usage::

		node.requires(Requirements.has_permission(1))

	.. seealso::

		Method :meth:`AbstractNode.requires() <mcdreforged.command.builder.nodes.basic.AbstractNode.requires>`,
		method :meth:`NodeDefinition.requires() <mcdreforged.command.builder.tools.NodeDefinition.requires>`

	.. versionadded:: v2.6.0
	"""

	@classmethod
	def has_permission(cls, level: int) -> Callable[[CommandSource], bool]:
		"""
		Check if the command source has the given permission level

		:param level: The minimum accepted permission level
		"""
		def callback(source: CommandSource) -> bool:
			return source.has_permission(level)
		return callback

	@classmethod
	def is_player(cls) -> Callable[[CommandSource], bool]:
		"""
		Check if the command source indicates a player
		"""
		def callback(source: CommandSource) -> bool:
			return source.is_player
		return callback

	@classmethod
	def is_console(cls) -> Callable[[CommandSource], bool]:
		"""
		Check if the command source indicates the console
		"""
		def callback(source: CommandSource) -> bool:
			return source.is_console
		return callback

	@classmethod
	def argument_exists(cls, arg_name: str) -> Callable[[CommandSource, dict], bool]:
		"""
		Check if the given argument has been assigned in current command context

		:param arg_name: The name of the argument to be checked
		"""
		def callback(_source: CommandSource, context: dict) -> bool:
			return arg_name in context
		return callback


NodeType = TypeVar('NodeType', bound=AbstractNode)
ArgNodeType = TypeVar('ArgNodeType', bound=ArgumentNode)
Self = TypeVar('Self', bound='NodeDefinition')


class NodeDefinition(Generic[NodeType], ABC):
	"""
	A node definition class holding extra customization information
	"""

	def post_process(self: Self, post_processor: Callable[[NodeType], Any]) -> Self:
		"""
		Added a post-process function to the current node definition

		During method :meth:`SimpleCommandBuilder.build`, after a node is constructed,
		all the post-process functions will be applied to the node object
		"""
		raise NotImplementedError()

	def requires(self: Self, requirement: REQUIRES_CALLBACK, failure_message_getter: Optional[FAIL_MSG_CALLBACK] = None) -> Self:
		"""
		See :meth:`AbstractNode.requires() <mcdreforged.command.builder.nodes.basic.AbstractNode.requires>`
		"""
		raise NotImplementedError()

	def suggests(self: Self, suggestion: SUGGESTS_CALLBACK) -> Self:
		"""
		See :meth:`AbstractNode.suggests() <mcdreforged.command.builder.nodes.basic.AbstractNode.suggests>`
		"""
		raise NotImplementedError()

	def on_error(self: Self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		"""
		See :meth:`AbstractNode.on_error() <mcdreforged.command.builder.nodes.basic.AbstractNode.on_error>`
		"""
		raise NotImplementedError()

	def on_child_error(self: Self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		"""
		See :meth:`AbstractNode.on_child_error() <mcdreforged.command.builder.nodes.basic.AbstractNode.on_child_error>`
		"""
		raise NotImplementedError()


class _NodeDefinitionImpl(NodeDefinition):
	def __init__(self, node_factory: Callable[[str], NodeType]):
		self.__node_factory = node_factory
		self.__node_processors: List[Callable[[NodeType], Any]] = []

	def create_node(self, node_name: str) -> NodeType:
		node = self.__node_factory(node_name)
		for processor in self.__node_processors:
			processor(node)
		return node

	def post_process(self, post_processor: Callable[[NodeType], Any]) -> Self:
		self.__node_processors.append(post_processor)
		return self

	def requires(self: Self, requirement: REQUIRES_CALLBACK, failure_message_getter: Optional[FAIL_MSG_CALLBACK] = None) -> Self:
		return self.post_process(lambda n: n.requires(requirement, failure_message_getter))

	def suggests(self: Self, suggestion: SUGGESTS_CALLBACK) -> Self:
		return self.post_process(lambda n: n.suggests(suggestion))

	def on_error(self: Self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		return self.post_process(lambda n: n.on_error(error_type, handler, handled=handled))

	def on_child_error(self: Self, error_type: Type[CommandError], handler: ERROR_HANDLER_CALLBACK, *, handled: bool = False) -> Self:
		return self.post_process(lambda n: n.on_child_error(error_type, handler, handled=handled))


class SimpleCommandBuilder:
	"""
	A tree-free command builder for easier command building. Declare & Define, that's all you need

	.. versionadded:: v2.6.0
	"""
	class Error(Exception):
		"""
		Custom exception to be thrown in :class:`SimpleCommandBuilder`
		"""
		pass

	__DEFAULT_LITERAL_DEFINITION = _NodeDefinitionImpl(Literal)

	def __init__(self):
		self.__commands: Dict[str, RUNS_CALLBACK] = {}
		self.__literals: Dict[str, _NodeDefinitionImpl[Literal]] = {}
		self.__arguments: Dict[str, _NodeDefinitionImpl[ArgumentNode]] = {}
		self.__build_cache: Optional[List[AbstractNode]] = None

	@classmethod
	def __is_arg(cls, node_name: str) -> bool:
		return len(node_name) > 0 and node_name[0] == '<' and node_name[-1] == '>'

	@classmethod
	def __make_arg(cls, arg_name: str) -> str:
		return '<{}>'.format(arg_name)

	@classmethod
	def __strip_arg(cls, node_name: str) -> str:
		return node_name[1:-1] if cls.__is_arg(node_name) else node_name

	def __clean_cache(self):
		self.__build_cache = None

	def __locate_or_create_child(self, parent: AbstractNode, node_name: str) -> AbstractNode:
		child_map: Dict[str, AbstractNode] = {}
		for child in parent.get_children():
			if isinstance(child, Literal):
				for literal in child.literals:
					child_map[literal] = child
			elif isinstance(child, ArgumentNode):
				child_map[self.__make_arg(child.get_name())] = child
			else:
				# it should never go here
				raise TypeError('Unexpected node type {}'.format(child.__class__))

		child = child_map.get(node_name)
		if child is None:
			child_factory: _NodeDefinitionImpl[AbstractNode]
			if self.__is_arg(node_name):
				child_factory = self.__arguments.get(node_name)
				if child_factory is None:
					raise self.Error('Undefined arg {}'.format(node_name))
			else:
				child_factory = self.__literals.get(node_name, self.__DEFAULT_LITERAL_DEFINITION)

			child = child_factory.create_node(self.__strip_arg(node_name))
			parent.then(child)

		return child

	# --------------
	#   Interfaces
	# --------------

	def command(self, command: str, callback: RUNS_CALLBACK):
		"""
		Define a command and its callback

		A command path string is made up of several elements separated by spaces.
		These elements are the names of corresponding command node. They describe a path from the root node
		to the target node in the command tree

		If a node has a name surrounding with ``"<"`` and ``">"``, it will be considered as an argument node, e.g. ``"<my_arg>"``.
		Otherwise it will be considered as a literal node, e.g. ``"my_literal"``

		You need to give definitions of argument nodes with the :meth:`arg` method.
		You can also define your custom literal nodes with the :meth:`literal` method

		:param command: A command path string, e.g. ``"!!calc add <value_a> <value_b>"``
		:param callback: The callback function of this command, which will be passed to :meth:`AbstractNode.then<mcdreforged.command.builder.nodes.basic.AbstractNode.then>`
		"""
		self.__commands[command] = callback
		self.__clean_cache()

	def arg(self, arg_name: str, node_factory: Callable[[str], ArgNodeType]) -> NodeDefinition[ArgNodeType]:
		"""
		Define an argument node for an argument name. All argument names appeared in :meth:`command` must be defined

		Notes that almost all MCDR builtin argument node classes can be constructed with 1 argument name parameter
		(e.g. :class:`~mcdreforged.command.builder.nodes.arguments.Text`, :class:`~mcdreforged.command.builder.nodes.arguments.Number`),
		so you can just use the name of the argument class here

		Examples::

			builder.arg('my_arg', QuotableText)
			builder.arg('my_arg', lambda name: Integer(name).at_min(0))

		:param arg_name: The name of the argument node. It can be quoted with ``"<>"`` if you want. Examples: ``"my_arg"``, ``"<my_arg>"``
		:param node_factory: An argument node constructor, that accepts the argument name as the only parameter
			and return an :class:`~mcdreforged.command.builder.nodes.basic.ArgumentNode` object
		:return: A :class:`NodeDefinition` object. With that you can further customize this node definition
		"""
		if not self.__is_arg(arg_name):
			arg_name = self.__make_arg(arg_name)
		definition = _NodeDefinitionImpl(node_factory)
		self.__arguments[arg_name] = definition
		self.__clean_cache()
		return definition

	def literal(self, literal_name: str, node_factory: Optional[Callable[[str], Literal]] = None) -> NodeDefinition[Literal]:
		"""
		Define a literal node for a literal name. It's useful when you want to have some custom literal nodes.
		If you just want a regular literal node, you don't need to invoke this method, since the builder will use
		the default :class:`~mcdreforged.command.builder.nodes.basic.Literal` constructor for node construction

		:param literal_name: The name of the literal node
		:param node_factory: A literal node constructor, that accepts the literal name as the only parameter
			and return a :class:`~mcdreforged.command.builder.nodes.basic.Literal` object. Optional
		:return: A :class:`NodeDefinitionImpl` object. With that you can further customize this node definition
		"""
		if node_factory is None:
			node_factory = Literal
		definition = _NodeDefinitionImpl(node_factory)
		self.__literals[literal_name] = definition
		self.__clean_cache()
		return definition

	# --------------
	#    Outputs
	# --------------

	def build(self) -> List[AbstractNode]:
		"""
		Build the command trees

		Nodes with same name will be reused. e.g. if you define 3 commands with path ``"!!foo"``, ``"!!foo bar"`` and "``!!foo baz"``,
		the root ``"!!foo"`` node will be reused, and there will be only 1 ``"!!foo"`` node eventually

		:return: A list of the built command tree root nodes. The result is cached until you instruct the builder again
		:raise SimpleCommandBuilder.Error: if there are undefined argument nodes
		"""
		if self.__build_cache is None:
			root = Literal('#TEMP')
			for command, callback in self.__commands.items():
				node = root
				for segment in command.split(' '):
					if len(segment) > 0:
						node = self.__locate_or_create_child(node, segment)
				node.runs(callback)
			self.__build_cache = root.get_children()
		return self.__build_cache

	def register(self, server: 'PluginServerInterface'):
		"""
		A helper method for lazyman, to build with method :meth:`build` and register built commands to the MCDR server

		:param server: The :class:`~mcdreforged.plugin.server_interface.PluginServerInterface` object of your plugin
		:raise SimpleCommandBuilder.Error: if build fails, or there are rooted non-literal nodes
		"""
		for node in self.build():
			if isinstance(node, Literal):
				server.register_command(node)
			else:
				raise self.Error('Not-literal root node is not supported'.format(node))

	def print_tree(self, line_writer: tree_printer.LineWriter):
		"""
		A helper method for lazyman, to build with method :meth:`build` and print the built command trees

		Example::

			builder.print_tree(server.logger.info)

		:param line_writer: A printer function that accepts a str
		:raise SimpleCommandBuilder.Error: if build fails
		"""
		for node in self.build():
			node.print_tree(line_writer)
