import json
import os
from abc import ABC
from pathlib import Path
from typing import IO, TYPE_CHECKING, Collection

from typing_extensions import override

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils import class_utils
from mcdreforged.utils.exception import IllegalPluginStructure

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class _DirectoryPluginBase(MultiFilePlugin, ABC):
	@override
	def open_file(self, file_path: str) -> IO[bytes]:
		return open(self._file_root / file_path, 'rb')

	@override
	def list_directory(self, directory_name: str) -> Collection[str]:
		return os.listdir(self._file_root / directory_name)

	@override
	def _check_subdir_legality(self):
		for package_name in os.listdir(self._file_root):
			path = self._file_root / package_name
			if path.is_dir():
				is_module = (path / '__init__.py').is_file()
				if is_module and package_name != self.get_id():
					raise IllegalPluginStructure('Packed plugin cannot contain other package: found package {}'.format(package_name))

	@override
	def file_exists(self):
		return self._file_root.is_dir()

	@override
	def file_changed(self):
		# It's not that easy to access all files in the directory
		# So just consider Directory Plugin to be always changed
		return True

	@override
	def calculate_file_modify_time(self):
		return None


class DirectoryPlugin(_DirectoryPluginBase):
	@override
	def get_type(self) -> PluginType:
		return PluginType.directory

	@property
	@override
	def _file_root(self) -> Path:
		return self.plugin_path


class LinkedDirectoryPlugin(_DirectoryPluginBase):
	def __init__(self, plugin_manager: 'PluginManager', file_path: Path):
		super().__init__(plugin_manager, file_path)
		self.link_file = file_path / plugin_constant.LINK_DIRECTORY_PLUGIN_FILE_NAME
		with open(self.link_file, 'r', encoding='utf8') as f:
			target = class_utils.check_type(json.load(f)['target'], str)
		self.target_plugin_path = Path(target)

	@override
	def get_type(self) -> PluginType:
		return PluginType.linked_directory

	@property
	@override
	def _file_root(self) -> Path:
		return self.target_plugin_path

	@override
	def file_exists(self):
		return self.link_file.is_file() and super().file_exists()

	@override
	def _create_repr_fields(self) -> dict:
		return {
			**super()._create_repr_fields(),
			'target': self.target_plugin_path,
		}
