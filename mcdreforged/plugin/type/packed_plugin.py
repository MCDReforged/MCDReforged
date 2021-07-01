import importlib
import json
import sys
from abc import ABC
from typing import IO

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils.exception import BrokenMetadata


class PackedPlugin(RegularPlugin, ABC):
	def get_fallback_metadata_id(self) -> str:
		raise BrokenMetadata('Missing plugin id in {}'.format(plugin_constant.PLUGIN_META_FILE))

	def get_file(self, file_name: str) -> IO[bytes]:
		raise NotImplementedError()

	def _get_module_instance(self):
		return importlib.import_module(self.get_id())

	def _on_load(self):
		super()._on_load()
		self._set_metadata(Metadata(self, json.load(self.get_file(plugin_constant.PLUGIN_META_FILE))))
		self._check_subdir_legality()

	def _on_unload(self):
		super()._on_unload()
		try:
			sys.path.remove(self.file_path)
		except ValueError:
			self.mcdr_server.logger.debug('Fail to remove path "{}" in sys.path for {}'.format(self.file_path, self))

	def _on_ready(self):
		sys.path.append(self.file_path)
		# It's fail-proof for packed plugin
		try:
			self._load_entry_instance()
		except:
			self.mcdr_server.logger.exception('Fail to load the entry point of {}'.format(self))
		else:
			super()._on_ready()

	def _check_subdir_legality(self):
		"""
		Make sure the only python submodule inside the plugin is named with the plugin id
		:raise IllegalPluginStructure if check failed
		"""
		raise NotImplementedError()
