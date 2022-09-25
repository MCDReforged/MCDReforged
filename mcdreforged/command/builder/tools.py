from typing import Dict, Callable, TYPE_CHECKING, Optional, List

from mcdreforged.command.builder.nodes.basic import RUNS_CALLBACK, Literal, AbstractNode, ArgumentNode

if TYPE_CHECKING:
	from mcdreforged.plugin.server_interface import PluginServerInterface
	from mcdreforged.utils import tree_printer


class SimpleCommandBuilder:
	class Error(Exception):
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

	# --------------
	#   Interfaces
	# --------------

	def command(self, command: str, callback: RUNS_CALLBACK) -> 'SimpleCommandBuilder':
		self.__commands[command] = callback
		self.__clean_cache()
		return self

	def literal(self, literal_name: str, node: Callable[[str], Literal]) -> 'SimpleCommandBuilder':
		self.__literals[literal_name] = node
		self.__clean_cache()
		return self

	def arg(self, arg_name: str, node: Callable[[str], ArgumentNode]) -> 'SimpleCommandBuilder':
		if not self.__is_arg(arg_name):
			arg_name = self.__make_arg(arg_name)
		self.__arguments[arg_name] = node
		self.__clean_cache()
		return self

	def __get_or_create_child(self, parent: AbstractNode, node_name: str) -> AbstractNode:
		child_map: Dict[str, AbstractNode] = {}
		for child in parent.get_children():
			if isinstance(child, Literal):
				for literal in child.literals:
					child_map[literal] = child
			elif isinstance(child, ArgumentNode):
				child_map[self.__make_arg(child.get_name())] = child
			else:
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
	#    Outputs
	# --------------

	def build(self) -> List[AbstractNode]:
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
		for node in self.build():
			if isinstance(node, Literal):
				server.register_command(node)
			else:
				raise self.Error('Not-literal root node is not supported'.format(node))

	def print_tree(self, line_printer: 'tree_printer.LineWriter'):
		for node in self.build():
			node.print_tree(line_printer)
