import os
from typing import IO

from mcdreforged.plugin.type.packed_plugin import PackedPlugin


class DirectoryPlugin(PackedPlugin):
	def get_file(self, file_name: str) -> IO[bytes]:
		return open(os.path.join(self.file_path, file_name), 'rb')

	def _check_subdir_legality(self):
		for package_name in os.listdir(self.file_path):
			path = os.path.join(self.file_path, package_name)
			if os.path.isdir(path):
				is_module = os.path.isfile(os.path.join(path, '__init__.py'))
				if is_module and package_name != self.get_id():
					raise Exception('Packed plugin cannot contain other package: found package {}'.format(package_name))

	def file_exists(self):
		return os.path.isdir(self.file_path)

	def file_changed(self):
		# It's not that easy to access all files in the directory
		return True

	def get_file_hash(self):
		return None