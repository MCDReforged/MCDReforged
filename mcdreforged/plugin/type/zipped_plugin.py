import os
import sys
import zipimport
from typing import IO
from zipfile import ZipFile

from mcdreforged.plugin.type.packed_plugin import PackedPlugin
from mcdreforged.utils.exception import IllegalPluginStructure


class ZippedPlugin(PackedPlugin):
	def get_file(self, file_name: str) -> IO[bytes]:
		return ZipFile(self.file_path).open(file_name, 'r')

	def _check_subdir_legality(self):
		zip_file = ZipFile(self.file_path)
		for file_info in zip_file.infolist():
			if file_info.is_dir():
				package_name = file_info.filename[:-1]  # removing the ending '/'
				try:
					init_info = zip_file.getinfo(os.path.join(package_name, '__init__.py'))
				except KeyError:
					is_module = False
				else:
					is_module = not init_info.is_dir()
				if is_module and package_name != self.get_id():
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(package_name))

	def _on_unload(self):
		super()._on_unload()
		try:
			for path in list(sys.path_importer_cache.keys()):
				if path.startswith(self.file_path):
					sys.path_importer_cache.pop(path)
			# noinspection PyProtectedMember,PyUnresolvedReferences
			zipimport._zip_directory_cache.pop(self.file_path)
		except KeyError:
			self.mcdr_server.logger.exception('Fail to clean zip import cache for {}'.format(self))
