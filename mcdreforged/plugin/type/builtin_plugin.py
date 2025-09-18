from abc import ABC
from typing import TYPE_CHECKING

from typing_extensions import override

from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel
from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.plugin import AbstractPlugin

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class BuiltinPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager: 'PluginManager', metadata_model: PluginMetadataJsonModel):
		super().__init__(plugin_manager)
		self._set_metadata(Metadata.create(metadata_model, plugin=self))

	@override
	def get_type(self) -> PluginType:
		return PluginType.builtin

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
