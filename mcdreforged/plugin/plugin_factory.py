import os
from typing import Optional, TYPE_CHECKING

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.type.directory_plugin import DirectoryPlugin
from mcdreforged.plugin.type.regular_plugin import RegularPlugin
from mcdreforged.plugin.type.solo_plugin import SoloPlugin
from mcdreforged.plugin.type.zipped_plugin import ZippedPlugin

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


def __get_suffix(file_path: str):
	index = file_path.rfind('.')
	if index == -1:
		return ''
	return file_path[index:]


def __get_plugin_class_from_path(file_path: str) -> Optional[type]:
	if os.path.isfile(file_path):
		suffix = __get_suffix(file_path)
		if suffix == plugin_constant.SOLO_PLUGIN_FILE_SUFFIX:
			return SoloPlugin
		if suffix == plugin_constant.PACKED_PLUGIN_FILE_SUFFIX:
			return ZippedPlugin
	elif os.path.isdir(file_path) and not file_path.endswith(plugin_constant.DISABLED_PLUGIN_FILE_SUFFIX):
		if os.path.isfile(os.path.join(file_path, plugin_constant.PLUGIN_META_FILE)):
			return DirectoryPlugin


def maybe_plugin(file_path: str) -> bool:
	return __get_plugin_class_from_path(file_path) is not None


def create_regular_plugin(plugin_manager: 'PluginManager', file_path: str) -> Optional[RegularPlugin]:
	cls = __get_plugin_class_from_path(file_path)
	if cls is None:
		return None
	return cls(plugin_manager, file_path)
