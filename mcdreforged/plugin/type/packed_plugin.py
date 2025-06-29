import contextlib
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

		for zip_info in self.__zip_file.infolist():
			path = zip_info.filename
			if zip_info.is_dir():
				continue

			file_path = Path(path)
			parts = file_path.parts
			if len(parts) == 1:
				if file_path.suffix == '.py' and file_path.stem != plugin_id:
					raise IllegalPluginStructure(f'Packed plugin cannot contain other module: found module {file_path.stem}')
			elif parts[0].startswith(('.', '__')):
				continue
			elif parts[0] != plugin_id:
				if file_path.suffix == '.py':
					raise IllegalPluginStructure(f'Packed plugin cannot contain other package: found package {".".join(parts[:-1])}')

	# noinspection PyProtectedMember,PyUnresolvedReferences
	@override
	def _on_unload(self):
		super()._on_unload()
		try:
			for path in list(sys.path_importer_cache.keys()):
				if path_utils.is_relative_to(Path(path), self.plugin_path):
					sys.path_importer_cache.pop(path)
			with contextlib.suppress(KeyError):
				cache: dict = zipimport._zip_directory_cache
				cache.pop(self._module_search_path)
		except KeyError:
			self.mcdr_server.logger.exception('Fail to clean zip import cache for {}'.format(self))

		if sys.version_info >= (3, 10):
			# https://github.com/MCDReforged/MCDReforged/issues/283
			try:
				from importlib.metadata import FastPath
				FastPath.__new__.cache_clear()
			except Exception:
				self.mcdr_server.logger.exception('Fail to clean the importlib internal path cache')
			else:
				import gc
				gc.collect()

	@override
	def _load_entry_instance(self):
		self.__file_sha256 = file_utils.calc_file_sha256(self.plugin_path)
		super()._load_entry_instance()

	def get_file_sha256(self) -> str:
		return self.__file_sha256
