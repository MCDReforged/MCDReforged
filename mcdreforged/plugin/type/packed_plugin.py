import importlib
import json
import os
import sys
from abc import ABC
from typing import IO, Collection

from ruamel import yaml

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils.exception import BrokenMetadata, IllegalPluginStructure


class PackedPlugin(RegularPlugin, ABC):
	def get_fallback_metadata_id(self) -> str:
		raise BrokenMetadata('Missing plugin id in {}'.format(plugin_constant.PLUGIN_META_FILE))

	def open_file(self, file_path: str) -> IO[bytes]:
		raise NotImplementedError()

	def list_directory(self, directory_name: str) -> Collection[str]:
		return os.listdir(os.path.join(self.plugin_path, directory_name))

	def _get_module_instance(self):
		return importlib.import_module(self.get_id())

	def _on_load(self):
		super()._on_load()
		try:
			meta_file = self.open_file(plugin_constant.PLUGIN_META_FILE)
		except KeyError:
			raise IllegalPluginStructure('Metadata file {} not found'.format(plugin_constant.PLUGIN_META_FILE)) from None
		self._set_metadata(Metadata(self, json.load(meta_file)))
		self._check_subdir_legality()

	def _on_unload(self):
		super()._on_unload()
		try:
			sys.path.remove(self.plugin_path)
		except ValueError:
			self.mcdr_server.logger.debug('Fail to remove path "{}" in sys.path for {}'.format(self.plugin_path, self))

	def _on_ready(self):
		sys.path.append(self.plugin_path)
		# It's fail-proof for packed plugin
		try:
			self._load_entry_instance()
		except:
			self.mcdr_server.logger.exception('Fail to load the entry point of {}'.format(self))
		else:
			super()._on_ready()
		self.__register_default_translation()

	def __register_default_translation(self):
		try:
			file_list = self.list_directory(plugin_constant.PLUGIN_TRANSLATION_FILES_PATH)
		except FileNotFoundError:
			return
		for file_name in file_list:
			try:
				language, file_extension = file_name.rsplit('.', 1)
				file_handler = self.open_file(os.path.join(plugin_constant.PLUGIN_TRANSLATION_FILES_PATH, file_name))
				if file_extension == 'json':
					translations = json.load(file_handler)
				elif file_extension == 'yml':
					translations = dict(yaml.round_trip_load(file_handler))
				else:
					continue
				self.register_translation(language, translations)
			except:
				self.mcdr_server.logger.exception('Fail to load default translation from file {}'.format(file_name))

	def _check_subdir_legality(self):
		"""
		Make sure the only python submodule inside the plugin is named with the plugin id
		:raise IllegalPluginStructure if check failed
		"""
		raise NotImplementedError()
