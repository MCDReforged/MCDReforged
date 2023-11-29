from typing import Iterable

from mcdreforged.command.builder.common import CommandContext, ParseResult
from mcdreforged.command.builder.nodes.basic import Literal


class CountingLiteral(Literal):
	"""
	A special literal node with an extra ability: store how many times it got visited
	during the command parsing in the command context
	"""
	def __init__(self, literal: str or Iterable[str], counter_key: str):
		super().__init__(literal)
		self.counter_key = counter_key

	def _on_visited(self, context: CommandContext, parsed_result: ParseResult):
		context[self.counter_key] = context.get(self.counter_key, 0) + 1

	def __repr__(self):
		return 'CountingLiteral[literals={},counter_key={}]'.format(self.literals, self.counter_key)
