from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
	from mcdreforged.info_reactor.info import Info
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class InfoFilter(ABC):
	@abstractmethod
	def filter_server_info(self, info: 'Info') -> bool:
		"""
		Filter an info object from the server output, check if it should be discarded

		If the server info object is discarded, it will not be echoed to the console output,
		and will not be processed by any of the remaining MCDR logic

		Do not affect innocent info objects; that is, do not discard those info that contains important messages (e.g. server start / stop),
		or MCDR might not work correctly

		This function is invoked right after an :class:`~mcdreforged.info_reactor.info.Info` object is parsed from server
		output

		:param info: The info object, which is parsed from server output, to check
		:return: True: do nothing; False: discard the info object
		"""
		...


class InfoFilterHolder(NamedTuple):
	filter: InfoFilter
	plugin: 'AbstractPlugin'
