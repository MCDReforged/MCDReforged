import typing
from contextlib import contextmanager
from typing import List, Iterable, Dict, Any, Optional, NamedTuple

from mcdreforged.command.command_source import CommandSource

if typing.TYPE_CHECKING:
	from mcdreforged.command.builder.nodes.basic import AbstractNode, ArgumentNode


class ParseResult(NamedTuple):
	value: Optional[Any]
	char_read: int


class CommandSuggestion:
	def __init__(self, command_read: str, suggest_segment: str):
		self.__command_read = command_read
		self.__suggest_segment = suggest_segment

	def __hash__(self):
		return hash(self.__suggest_segment) + hash(self.__command_read) * 31

	def __eq__(self, other):
		return isinstance(other, type(self)) and self.__dict__ == other.__dict__

	@property
	def command(self) -> str:
		return self.__command_read + self.__suggest_segment

	@property
	def existed_input(self) -> str:
		return self.__command_read

	@property
	def suggest_input(self) -> str:
		return self.__suggest_segment

	def __str__(self):
		return '{} -> {}'.format(self.__command_read, self.__suggest_segment)


class CommandSuggestions(List[CommandSuggestion]):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		# !!MCDR plg load <file_name>
		#                 ^
		#               cursor
		# "<file_name>" is the complete_hint
		self.complete_hint: Optional[str] = None

	def extend(self, __iterable: Iterable) -> None:
		super().extend(__iterable)
		if isinstance(__iterable, CommandSuggestions):
			self.complete_hint = self.complete_hint or __iterable.complete_hint


class CommandContext(Dict[str, Any]):
	def __init__(self, source: 'CommandSource', command: str):
		super().__init__()
		self.__source = source
		self.__command = command
		self.__cursor = 0
		self.__node_path = []  # type: List[AbstractNode]

	def copy(self) -> 'CommandContext':
		copied = CommandContext(self.source, self.command)
		copied.update(self)
		copied.__cursor = self.__cursor
		copied.__node_path = self.__node_path.copy()
		return copied

	@property
	def source(self) -> 'CommandSource':
		return self.__source

	@property
	def command(self) -> str:
		return self.__command

	@property
	def command_read(self) -> str:
		return self.__command[:self.__cursor]

	@property
	def command_remaining(self) -> str:
		return self.__command[self.__cursor:]

	@property
	def cursor(self) -> int:
		return self.__cursor

	@property
	def node_path(self) -> List['AbstractNode']:
		return self.__node_path

	# -------------------------
	#      Not public APIs
	# -------------------------

	@contextmanager
	def read_command(self, current_node: 'AbstractNode', result: 'ParseResult', new_cursor: int):
		"""
		**Not public API, only used in command parsing**
		Change the current cursor position, and store the parsing value
		"""
		from mcdreforged.command.builder.nodes.basic import ArgumentNode

		prev_cursor = self.__cursor
		self.__cursor = new_cursor

		if isinstance(current_node, ArgumentNode):
			self[current_node.get_name()] = result.value
		try:
			yield
		finally:
			self.__cursor = prev_cursor
			if isinstance(current_node, ArgumentNode):
				self.pop(current_node.get_name(), None)

	@contextmanager
	def enter_child(self, node: 'AbstractNode'):
		"""
		**Not public API, only used in command parsing**
		Enter a command node, maintain the node_path
		"""
		self.__node_path.append(node)
		try:
			yield
		finally:
			self.__node_path.pop(len(self.__node_path) - 1)
