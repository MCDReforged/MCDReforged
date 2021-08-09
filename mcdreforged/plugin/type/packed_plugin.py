import os
import sys
import zipimport
from io import BytesIO
from typing import IO, Collection, TYPE_CHECKING, Optional
from zipfile import ZipFile

from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils.exception import IllegalPluginStructure

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class PackedPlugin(MultiFilePlugin):
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		super().__init__(plugin_manager, file_path)
		self.__zip_file_cache = None  # type: Optional[ZipFile]

	@property
	def __zip_file(self) -> ZipFile:
		if self.__zip_file_cache is None:
			with open(self.plugin_path, 'rb') as file_handler:
				content = BytesIO()
				content.write(file_handler.read())
			self.__zip_file_cache = ZipFile(content)
		return self.__zip_file_cache

	@classmethod
	def __format_path(cls, path: str):
		return path.replace('\\', '/')

	def _reset(self):
		super()._reset()
		if self.__zip_file_cache is not None:
			self.__zip_file_cache.close()
		self.__zip_file_cache = None

	def open_file(self, file_path: str) -> IO[bytes]:
		return self.__zip_file.open(self.__format_path(file_path), 'r')

	def list_directory(self, directory_name: str) -> Collection[str]:
		result = []
		directory_name = self.__format_path(directory_name).rstrip('/\\') + '/'
		for file_info in self.__zip_file_cache.infolist():
			# is inside the dir and is directly inside
			if file_info.filename.startswith(directory_name):
				file_name = file_info.filename.replace(directory_name, '', 1)
				if len(file_name) > 0 and '/' not in file_name.rstrip('/'):
					result.append(file_name)
		return result

	def _check_subdir_legality(self):
		for file_info in self.__zip_file_cache.infolist():
			if file_info.is_dir():
				package_name: str = file_info.filename[:-1]  # removing the ending '/'
				if '/' in package_name:  # not at root
					continue
				try:
					init_info = self.__zip_file_cache.getinfo(os.path.join(package_name, '__init__.py'))
				except KeyError:
					is_module = False
				else:
					is_module = not init_info.is_dir()
				if is_module and package_name != self.get_id():
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(package_name))

	# noinspection PyProtectedMember,PyUnresolvedReferences
	def _on_unload(self):
		super()._on_unload()
		try:
			for path in list(sys.path_importer_cache.keys()):
				if path.startswith(self.plugin_path):
					sys.path_importer_cache.pop(path)
			if self.plugin_path in zipimport._zip_directory_cache:
				zipimport._zip_directory_cache.pop(self.plugin_path)
		except KeyError:
			self.mcdr_server.logger.exception('Fail to clean zip import cache for {}'.format(self))
