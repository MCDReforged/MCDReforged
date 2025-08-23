import contextlib
import functools
import os
import sys
import zipimport
from io import BytesIO
from pathlib import Path
from typing import IO, Collection, TYPE_CHECKING, Optional
from zipfile import ZipFile

from typing_extensions import override

from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils import path_utils, file_utils
from mcdreforged.utils.exception import IllegalPluginStructure

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager

_LRU_FUNC_TYPE = type(functools.lru_cache(maxsize=None)(lambda: None))


class PackedPlugin(MultiFilePlugin):
	def __init__(self, plugin_manager: 'PluginManager', file_path: Path):
		super().__init__(plugin_manager, file_path)
		self.__zip_file_cache: Optional[ZipFile] = None
		self.__file_sha256: Optional[str] = None

	@override
	def get_type(self) -> PluginType:
		return PluginType.packed

	@property
	def __zip_file(self) -> ZipFile:
		if self.__zip_file_cache is None:
			with open(self.plugin_path, 'rb') as file_handler:
				content = BytesIO()
				content.write(file_handler.read())
			self.__zip_file_cache = ZipFile(content)
		return self.__zip_file_cache

	@classmethod
	def __format_path(cls, path: str) -> str:
		return path.replace('\\', '/')

	@override
	def _reset(self):
		super()._reset()
		if self.__zip_file_cache is not None:
			self.__zip_file_cache.close()
		self.__zip_file_cache = None

	@override
	def open_file(self, file_path: str) -> IO[bytes]:
		return self.__zip_file.open(self.__format_path(file_path), 'r')

	@override
	def list_directory(self, directory_name: str) -> Collection[str]:
		result = []
		directory_name = self.__format_path(directory_name).rstrip('/\\') + '/'
		for file_info in self.__zip_file.infolist():
			# is inside the dir and is directly inside
			if file_info.filename.startswith(directory_name):
				file_name = file_info.filename.replace(directory_name, '', 1)
				if len(file_name) > 0 and '/' not in file_name.rstrip('/'):
					result.append(file_name)
		return result

	@override
	def _check_dir_legality(self):
		plugin_id = self.get_id()
		for file_info in self.__zip_file.infolist():
			name = file_info.filename.rstrip('/')
			if '/' in name: # not at root
				continue
			if file_info.is_dir():
				try:
					init_info = self.__zip_file.getinfo(os.path.join(name, '__init__.py'))
				except KeyError:
					is_module = False
				else:
					is_module = not init_info.is_dir()
				if is_module and name != plugin_id:
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(name))
			elif name.endswith('.py'):
				module_name = name[:-3]  # remove .py
				if module_name != plugin_id and self._ILLEGAL_ROOT_PY_FILE_STEM.fullmatch(module_name):
					raise IllegalPluginStructure('Packed plugin cannot contain other module: found module {} at {}'.format(module_name, name))

	@override
	def _on_unload(self):
		super()._on_unload()
		try:
			for path in list(sys.path_importer_cache.keys()):
				if path_utils.is_relative_to(Path(path), self.plugin_path):
					sys.path_importer_cache.pop(path)
			with contextlib.suppress(KeyError):
				# noinspection PyProtectedMember,PyUnresolvedReferences
				cache: dict = zipimport._zip_directory_cache
				cache.pop(self._module_search_path)
		except KeyError:
			self.mcdr_server.logger.exception('Fail to clean zip import cache for {}'.format(self))

		self.release_file_occupation()

	@override
	def _load_entry_instance(self):
		self.__file_sha256 = file_utils.calc_file_sha256(self.plugin_path)
		super()._load_entry_instance()

	def get_file_sha256(self) -> str:
		return self.__file_sha256

	def release_file_occupation(self):
		"""
		Make the best effort to close all open file handles related to the packed plugin file,
		to prevent the Windows error "The process cannot access the file because it is being used by another process"
		during operations on the packed plugin file
		"""

		def release_importlib_zip_path_cache():
			if sys.version_info < (3, 10):
				return

			# https://github.com/MCDReforged/MCDReforged/issues/283
			try:
				# noinspection PyProtectedMember,PyUnresolvedReferences
				from importlib.metadata import FastPath
				lru_func: _LRU_FUNC_TYPE = FastPath.__new__

				if lru_func.cache_info().currsize == 0:
					return

				lru_func.cache_clear()
			except Exception:
				self.mcdr_server.logger.exception('Fail to clean the importlib internal path cache')
			else:
				import gc
				gc.collect()

		release_importlib_zip_path_cache()
