import os
from typing import IO

from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils.exception import IllegalPluginStructure


class DirectoryPlugin(MultiFilePlugin):
	def open_file(self, file_path: str) -> IO[bytes]:
		return open(os.path.join(self.plugin_path, file_path), 'rb')

	def _check_subdir_legality(self):
		for package_name in os.listdir(self.plugin_path):
			path = os.path.join(self.plugin_path, package_name)
			if os.path.isdir(path):
				is_module = os.path.isfile(os.path.join(path, '__init__.py'))
				if is_module and package_name != self.get_id():
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(package_name))

	def plugin_exists(self):
		return os.path.isdir(self.plugin_path)

	def file_changed(self):
		# It's not that easy to access all files in the directory
		# So just consider Directory Plugin to be always changed
		return True

	def calculate_file_modify_time(self):
		return None
