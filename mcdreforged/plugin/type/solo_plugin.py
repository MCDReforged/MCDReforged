import re

from mcdreforged.constants import core_constant
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils import misc_util, string_util


class SoloPlugin(RegularPlugin):
	def get_fallback_metadata_id(self) -> str:
		file_name = string_util.remove_suffix(self.file_name, core_constant.SOLO_PLUGIN_FILE_SUFFIX)
		return re.sub(r'[^a-z0-9]', '_', file_name.lower())

	def _get_module_instance(self):
		return misc_util.load_source(self.file_path)

	def _on_load(self):
		self._reset()
		self._load_instance()

	def _on_unload(self):
		self._unload_instance()

	def _on_ready(self):
		self._register_default_listeners()
