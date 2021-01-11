from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class AbstractInfoReactor:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server

	def react(self, info):
		raise NotImplementedError()
