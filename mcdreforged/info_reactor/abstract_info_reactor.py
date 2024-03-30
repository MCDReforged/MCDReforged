from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from mcdreforged.info_reactor.info import Info

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class AbstractInfoReactor(ABC):
	"""
	The abstract base class for info reactors
	"""

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server: 'MCDReforgedServer' = mcdr_server
		"""The MCDR server object"""

	@abstractmethod
	def react(self, info: Info):
		"""
		React to an :class:`~mcdreforged.info_reactor.info.Info` object

		It will be invoked on the task executor thread

		:param info: The info to be reacted to
		"""
		raise NotImplementedError()

	def on_server_start(self):
		"""
		Gets invoked when the server starts
		"""
		pass

	def on_server_stop(self):
		"""
		Gets invoked when the server stops
		"""
		pass
