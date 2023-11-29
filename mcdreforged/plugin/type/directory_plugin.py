import json
import os
from abc import ABC
from typing import IO, TYPE_CHECKING

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils import class_util
from mcdreforged.utils.exception import IllegalPluginStructure

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class _DirectoryPluginBase(MultiFilePlugin, ABC):
	def open_file(self, file_path: str) -> IO[bytes]:
		return open(os.path.join(self._file_root, file_path), 'rb')

	def _check_subdir_legality(self):
		for package_name in os.listdir(self._file_root):
			path = os.path.join(self._file_root, package_name)
			if os.path.isdir(path):
				is_module = os.path.isfile(os.path.join(path, '__init__.py'))
				if is_module and package_name != self.get_id():
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(package_name))

	def plugin_exists(self):
		return os.path.isdir(self._file_root)

	def file_changed(self):
		# It's not that easy to access all files in the directory
		# So just consider Directory Plugin to be always changed
		return True

	def calculate_file_modify_time(self):
		return None


class DirectoryPlugin(_DirectoryPluginBase):
	@property
	def _file_root(self) -> str:
		return self.plugin_path


class LinkedDirectoryPlugin(_DirectoryPluginBase):
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		super().__init__(plugin_manager, file_path)
		self.link_file = os.path.join(file_path, plugin_constant.LINK_DIRECTORY_PLUGIN_FILE_NAME)
		with open(self.link_file, 'r', encoding='utf8') as f:
			self.target_plugin_path = class_util.check_type(json.load(f)['target'], str)

	@property
	def _file_root(self) -> str:
		return self.target_plugin_path

	def plugin_exists(self):
		return os.path.isfile(self.link_file) and super().plugin_exists()