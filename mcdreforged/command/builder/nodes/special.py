from typing import Iterable

from typing_extensions import override

from mcdreforged.command.builder.common import CommandContext, ParseResult
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.utils import class_utils


class CountingLiteral(Literal):
	"""
	A special literal node with an extra ability: store how many times it got visited
	during the command parsing in the command context

	.. versionadded:: v2.12.0
	"""
	def __init__(self, literal: str or Iterable[str], counter_key: str):
		super().__init__(literal)
		self.counter_key = counter_key

	@override
	def _on_visited(self, context: CommandContext, parsed_result: ParseResult):
		context[self.counter_key] = context.get(self.counter_key, 0) + 1

	def __str__(self):
		literal = repr(tuple(self.literals)[0]) if len(self.literals) == 1 else set(self.literals)
		return 'CountingLiteral {} <{}>'.format(literal, self.counter_key)

	def __repr__(self):
		return class_utils.represent(self, {
			'literals': self.literals,
			'counter_key': self.counter_key,
		})
