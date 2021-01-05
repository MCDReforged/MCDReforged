import sys
from typing import Dict, List, Tuple

from mcdreforged.command.builder import command_builder_util as utils
from mcdreforged.command.builder.command_node import Literal
from mcdreforged.command.builder.exception import CommandError
from mcdreforged.command.command_source import CommandSource


class CommandExecutor:
	def __init__(self):
		self.root_nodes = {}  # type: Dict[str, List[Literal]]

	def add_root_node(self, node: Literal):
		if not isinstance(node, Literal):
			raise TypeError('Only Literal node is accpeted to be a root node')
		for literal in node.literals:
			nodes = self.root_nodes.get(literal, [])
			nodes.append(node)
			self.root_nodes[literal] = nodes

	def clear(self):
		self.root_nodes.clear()

	def execute(self, source: CommandSource, command: str) -> Tuple[List[CommandError], List]:
		first_literal_element = utils.get_element(command)
		errors = []
		general_exc_info = []
		for node in self.root_nodes.get(first_literal_element, []):
			try:
				node.execute(source, command)
			except CommandError as e:
				errors.append(e)
			except:
				general_exc_info.append(sys.exc_info())
		return errors, general_exc_info
