from typing import Dict, Callable, TYPE_CHECKING, Optional, List

from mcdreforged.command.builder.nodes.basic import RUNS_CALLBACK, Literal, AbstractNode, ArgumentNode
from mcdreforged.utils import tree_printer

if TYPE_CHECKING:
	from mcdreforged.plugin.server_interface import PluginServerInterface


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

	def __init__(self):
		self.__commands: Dict[str, RUNS_CALLBACK] = {}
		self.__literals: Dict[str, Callable[[str], Literal]] = {}
		self.__arguments: Dict[str, Callable[[str], ArgumentNode]] = {}
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

	def __get_or_create_child(self, parent: AbstractNode, node_name: str) -> AbstractNode:
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
			child_factory: Callable[[str], AbstractNode]
			if self.__is_arg(node_name):
				child_factory = self.__arguments.get(node_name)
				if child_factory is None:
					raise self.Error('Undefined arg {}'.format(node_name))
			else:
				child_factory = self.__literals.get(node_name, Literal)

			child = child_factory(self.__strip_arg(node_name))
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

	def arg(self, arg_name: str, node: Callable[[str], ArgumentNode]):
		"""
		Define an argument node for an argument name. All argument names appeared in :meth:`command` must be defined

		Notes that almost all MCDR builtin argument node classes can be constructed with 1 argument name parameter
		(e.g. :class:`~mcdreforged.command.builder.nodes.arguments.Text`, :class:`~mcdreforged.command.builder.nodes.arguments.Number`),
		so you can just use the name of the argument class here

		Examples::

			builder.arg('my_arg', QuotableText)
			builder.arg('my_arg', lambda name: Integer(name).at_min(0))

		:param arg_name: The name of the argument node. It can be quoted with ``"<>"`` if you want. Examples: ``"my_arg"``, ``"<my_arg>"``
		:param node: An argument node constructor, that accepts the argument name as the only parameter
			and return an :class:`~mcdreforged.command.builder.nodes.basic.ArgumentNode` object
		"""
		if not self.__is_arg(arg_name):
			arg_name = self.__make_arg(arg_name)
		self.__arguments[arg_name] = node
		self.__clean_cache()

	def literal(self, literal_name: str, node: Callable[[str], Literal]):
		"""
		Define a literal node for a literal name. It's useful when you want to have some custom literal nodes.
		If you just want a regular literal node, you don't need to invoke this method, since the builder will use
		the default :class:`~mcdreforged.command.builder.nodes.basic.Literal` constructor for node construction

		:param literal_name: The name of the literal node
		:param node: A literal node constructor, that accepts the literal name as the only parameter
			and return a :class:`~mcdreforged.command.builder.nodes.basic.Literal` object
		"""
		self.__literals[literal_name] = node
		self.__clean_cache()

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
						node = self.__get_or_create_child(node, segment)
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
