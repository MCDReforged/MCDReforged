import importlib.machinery
import importlib.machinery
import importlib.util
import re
import sys
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

from typing_extensions import override

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils import string_utils

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class SoloPlugin(RegularPlugin):
	def __init__(self, plugin_manager: 'PluginManager', file_path: Path):
		super().__init__(plugin_manager, file_path)
		self.module_name = 'MCDR_SOLO_PLUGIN@{}'.format(self.plugin_path)

	@override
	def get_type(self) -> PluginType:
		return PluginType.solo

	@override
	def get_fallback_metadata_id(self) -> str:
		file_name = string_utils.remove_suffix(self.file_name, plugin_constant.SOLO_PLUGIN_FILE_SUFFIX)
		return re.sub(r'[^a-z0-9]', '_', file_name.lower())

	@override
	def is_own_module(self, module_name: str) -> bool:
		return module_name == self.module_name

	@override
	def _import_entrypoint_module(self) -> ModuleType:
		if not self.plugin_path.is_file():
			raise TypeError('Source path {} of {} is not a file'.format(self.plugin_path, self))

		# https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
		# https://docs.python.org/zh-cn/3.6/library/importlib.html#importing-a-source-file-directly
		spec = importlib.util.spec_from_file_location(self.module_name, self.plugin_path)
		module = importlib.util.module_from_spec(spec)
		# noinspection PyUnresolvedReferences
		spec.loader.exec_module(module)
		# store the module, in case something want to access sys.modules[some_field.__module__]
		# e.g. typing.get_type_hints
		sys.modules[self.module_name] = module
		return module

	@override
	def _on_load(self):
		super()._on_load()
		self._load_entry_instance()
		meta_dict = getattr(self.entry_module_instance, 'PLUGIN_METADATA', {})
		self._set_metadata(Metadata(meta_dict, plugin=self))
