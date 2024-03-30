from abc import ABC
from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.plugin import AbstractPlugin

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class PermanentPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__(plugin_manager)
		self.__metadata: Optional[Metadata] = None

	def _set_metadata(self, metadata: Metadata):
		"""
		Needs to be called inside __init__ after super call
		"""
		# TODO: change constructor signature
		self.__metadata = metadata

	@override
	def get_metadata(self) -> Metadata:
		if self.__metadata is None:
			raise RuntimeError('accessing metadata before initialized')
		return self.__metadata

	@override
	def get_fallback_metadata_id(self) -> str:
		raise NotImplementedError()

	@override
	def ready(self):
		pass

	@override
	def reload(self):
		pass

	@override
	def unload(self):
		pass

	@override
	def remove(self):
		pass
