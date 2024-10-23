import importlib
import json
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path
from types import ModuleType
from typing import IO, Collection

from ruamel.yaml import YAML
from typing_extensions import override

from mcdreforged.constants import plugin_constant
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.plugin.exception import RequirementCheckFailure
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.utils import path_utils
from mcdreforged.utils.exception import BrokenMetadata, IllegalPluginStructure


class MultiFilePlugin(RegularPlugin, ABC):
	@property
	def _file_root(self) -> Path:
		return self.plugin_path

	@property
	def _module_search_path(self) -> str:
		return str(self._file_root)

	@override
	def get_fallback_metadata_id(self) -> str:
		raise BrokenMetadata('Missing plugin id in {}'.format(plugin_constant.PLUGIN_META_FILE))

	@abstractmethod
	def open_file(self, file_path: str) -> IO[bytes]:
		raise NotImplementedError()

	@abstractmethod
	def list_directory(self, directory_name: str) -> Collection[str]:
		raise NotImplementedError()

	@override
	def is_own_module(self, module_name: str) -> bool:
		plugin_id = self.get_id()
		return module_name == plugin_id or module_name.startswith('{}.'.format(plugin_id))

	@override
	def _import_entrypoint_module(self) -> ModuleType:
		mod = importlib.import_module(self.get_metadata().entrypoint)
		if mod.__file__ is not None:
			mod_path = Path(mod.__file__).absolute()
			file_root = Path(self._file_root).absolute()
			if file_root != mod_path and not path_utils.is_relative_to(mod_path, file_root):
				self.mcdr_server.logger.warning('Suspicious entrypoint module path for plugin %s, package name conflict?', self)
				self.mcdr_server.logger.warning('- Plugin file root: %s', file_root)
				self.mcdr_server.logger.warning('- Loaded entrypoint path: %s', mod_path)
		return mod

	@override
	def _on_load(self):
		super()._on_load()
		try:
			meta_file = self.open_file(plugin_constant.PLUGIN_META_FILE)
		except Exception:
			raise IllegalPluginStructure('Metadata file {} not found'.format(plugin_constant.PLUGIN_META_FILE)) from None
		with meta_file:
			self._set_metadata(Metadata(json.load(meta_file), plugin=self))
		self.__check_requirements()
		self._check_subdir_legality()

	@override
	def _on_unload(self):
		super()._on_unload()
		try:
			sys.path.remove(self._module_search_path)
		except ValueError:
			self.mcdr_server.logger.debug('Fail to remove path "{}" in sys.path for {}'.format(self._module_search_path, self))

	@override
	def _on_ready(self):
		sys.path.append(self._module_search_path)
		# It's fail-proof for packed plugin
		try:
			self._load_entry_instance()
		except Exception:
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
			file_path = os.path.join(plugin_constant.PLUGIN_TRANSLATION_FILES_PATH, file_name)
			try:
				language, file_extension = file_name.rsplit('.', 1)
				with self.open_file(file_path) as file_handler:
					if file_extension == 'json':
						translations = json.load(file_handler)
					elif file_extension in ['yml', 'yaml']:
						translations = dict(YAML().load(file_handler))
					else:
						self.mcdr_server.logger.mdebug('Skipping unknown translation file {} in {}'.format(file_path, repr(self)), option=DebugOption.PLUGIN)
						continue
				self.register_translation(language, translations)
			except Exception:
				self.mcdr_server.logger.exception('Fail to load default translation from file {} in {}'.format(file_path, repr(self)))

	def _check_subdir_legality(self):
		"""
		Make sure the only python submodule inside the plugin is named with the plugin id
		:raise IllegalPluginStructure if check failed
		"""
		raise NotImplementedError()

	def __check_requirements(self):
		try:
			req_file = self.open_file(plugin_constant.PLUGIN_REQUIREMENTS_FILE)
		except Exception:
			return
		with req_file:
			import packaging.requirements as pr
			import packaging.version as pv
			import importlib.metadata as im

			req_file_str = req_file.read().decode('utf8')
			for i, line in enumerate(req_file_str.splitlines()):
				# ref: pip._internal.req.req_file.ignore_comments
				line = line.split('#', 1)[0].strip()
				if len(line) == 0:
					continue

				try:
					req = pr.Requirement(line)  # InvalidRequirement
					dist = im.distribution(req.name)  # PackageNotFoundError
					version = pv.Version(dist.version)  # InvalidVersion
					if not req.specifier.contains(version, True):
						raise RequirementCheckFailure('version unsatisfied for required package {}: expect {}, but installed {}'.format(
							repr(req.name), repr(str(req.specifier)), repr(version)
						))
				except pr.InvalidRequirement as e:
					# no raise here, since we don't fully support the complete requirements.txt schema
					self.mcdr_server.logger.warning('Invalid / Unsupported requirement declaration {} in line {}:'.format(repr(line), i + 1))
					for err_line in str(e).splitlines():
						self.mcdr_server.logger.warning('    {}'.format(err_line))
				except im.PackageNotFoundError as e:
					raise RequirementCheckFailure('required package {} not installed'.format(repr(str(e))))
				except pv.InvalidVersion as e:
					raise RequirementCheckFailure('installed package {} version {} does not conform to PEP 440: {}'.format(
						repr(req.name), repr(dist.version), e
					))
