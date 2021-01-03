from typing import Dict, List

from mcdr.command.builder.command_node import Literal
from mcdr.command.builder.exception import CommandError
from mcdr.command.command_source import CommandSource


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

	def execute(self, source: CommandSource, command: str) -> List[CommandError]:
		first_literal_element = command.split(' ', 1)[0]
		errors = []
		for node in self.root_nodes.get(first_literal_element, []):
			try:
				node.execute(source, command)
			except CommandError as e:
				errors.append(e)
		return errors
