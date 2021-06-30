import os
from typing import IO

from mcdreforged.plugin.type.packed_plugin import PackedPlugin


class DirectoryPlugin(PackedPlugin):
	def get_file(self, file_name: str) -> IO[bytes]:
		return open(os.path.join(self.file_path, file_name))

	def file_exists(self):
		return os.path.isdir(self.file_path)

	def file_changed(self):
		# It's not that easy to access all files in the directory
		return True

	def get_file_hash(self):
		return None
