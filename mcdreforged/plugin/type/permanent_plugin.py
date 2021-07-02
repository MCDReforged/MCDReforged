from abc import ABC

from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.plugin import AbstractPlugin


class PermanentPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager, '**_builtin_**')
		self.__metadata = None

	def _set_metadata(self, metadata: Metadata):
		"""
		Needs to be called inside __init__ after super call
		"""
		self.__metadata = metadata

	def is_permanent(self) -> bool:
		return True

	def get_metadata(self) -> Metadata:
		return self.__metadata

	def get_fallback_metadata_id(self) -> str:
		raise RuntimeError()

	def ready(self):
		pass

	def reload(self):
		pass

	def unload(self):
		pass

	def remove(self):
		pass
