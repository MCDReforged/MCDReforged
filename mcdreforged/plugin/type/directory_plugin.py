import json
import os
from abc import ABC
from pathlib import Path
from typing import IO, TYPE_CHECKING, Collection

from typing_extensions import override

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.type.common import PluginType
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils.exception import IllegalPluginStructure
from mcdreforged.utils.serializer import Serializable

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
	def _check_dir_legality(self):
		plugin_id = self.get_id()
		for name in os.listdir(self._file_root):
			path = self._file_root / name
			if path.is_dir():
				is_module = (path / '__init__.py').is_file()
				if is_module and name != plugin_id:
					raise IllegalPluginStructure('Directory plugin cannot contain other package: found package {} at {}'.format(name, path))
			else:
				if path.suffix == '.py' and path.stem != plugin_id and self._ILLEGAL_ROOT_PY_FILE_STEM.fullmatch(path.stem):
					raise IllegalPluginStructure('Directory plugin cannot contain other module: found module {} at {}'.format(path.stem, path))

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


class LinkedDirectoryPluginMeta(Serializable):
	target: str
	skip_package_legality_check: bool = False


class LinkedDirectoryPlugin(_DirectoryPluginBase):
	def __init__(self, plugin_manager: 'PluginManager', file_path: Path):
		super().__init__(plugin_manager, file_path)
		self.link_file = file_path / plugin_constant.LINK_DIRECTORY_PLUGIN_FILE_NAME
		self.__ldp_meta = self.__read_ldp_meta()

	def __read_ldp_meta(self) -> LinkedDirectoryPluginMeta:
		with open(self.link_file, 'r', encoding='utf8') as f:
			return LinkedDirectoryPluginMeta.deserialize(json.load(f))

	@property
	def target_plugin_path(self) -> Path:
		return Path(self.__ldp_meta.target)

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

	@override
	def _check_dir_legality(self):
		if not self.__ldp_meta.skip_package_legality_check:
			super()._check_dir_legality()

	@override
	def _on_load(self):
		self.__ldp_meta = self.__read_ldp_meta()
		super()._on_load()
