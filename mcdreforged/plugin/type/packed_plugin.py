import importlib
import json
import sys
from typing import IO
from zipfile import ZipFile

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils.exception import BrokenMetadata


class PackedPlugin(RegularPlugin):
	def get_fallback_metadata_id(self) -> str:
		raise BrokenMetadata('Missing plugin id in {}'.format(plugin_constant.PLUGIN_META_FILE))

	def get_file(self, file_name: str) -> IO[bytes]:
		return ZipFile(self.file_path).open(file_name, 'r')

	def _get_module_instance(self):
		return importlib.import_module(self.get_id())

	def _on_load(self):
		self._reset()
		self._set_metadata(Metadata(self, json.load(self.get_file(plugin_constant.PLUGIN_META_FILE))))

	def _on_unload(self):
		self._unload_instance()
		sys.path.remove(self.file_path)

	def _on_ready(self):
		sys.path.append(self.file_path)
		# It's fail-proof for packed plugin
		try:
			self._load_instance()
		except:
			self.mcdr_server.logger.exception('Fail to load the entry point of {}'.format(self))
		else:
			self._register_default_listeners()

