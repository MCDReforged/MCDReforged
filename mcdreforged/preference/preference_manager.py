import json
from pathlib import Path
from typing import Optional, Dict, TYPE_CHECKING, Union

from mcdreforged.command.command_source import CommandSource, PlayerCommandSource, ConsoleCommandSource
from mcdreforged.constants import core_constant, plugin_constant
from mcdreforged.utils import file_utils
from mcdreforged.utils.serializer import Serializable, deserialize, serialize

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class PreferenceItem(Serializable):
	language: Optional[str]


class InvalidPreferenceSource(TypeError):
	pass


PREFERENCE_FILE_PATH = Path(plugin_constant.PLUGIN_CONFIG_DIRECTORY) / core_constant.PACKAGE_NAME / 'preferences.json'
CONSOLE_ALIAS = '#@MCDR_Console@#'
PreferenceStorage = Dict[str, PreferenceItem]
PreferenceSource = Union[str, CommandSource]


class PreferenceManager:
	"""
	.. versionadded:: v2.1.0
	"""
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server: 'MCDReforgedServer' = mcdr_server
		self.logger = mcdr_server.logger
		self.preferences: PreferenceStorage = {}
		self.__store_file_path = PREFERENCE_FILE_PATH

	def load_preferences(self):
		try:
			with open(self.__store_file_path, 'r', encoding='utf8') as file:
				self.preferences = deserialize(json.load(file), PreferenceStorage, error_at_missing=True, error_at_redundancy=True)
		except Exception as e:
			if not isinstance(e, FileNotFoundError):
				self.logger.exception('Failed to load preference file')
			self.preferences = {}
			self.__save_preferences()

	def __save_preferences(self):
		try:
			self.__store_file_path.parent.mkdir(exist_ok=True, parents=True)
			with file_utils.safe_write(self.__store_file_path, encoding='utf8') as file:
				json.dump(serialize(self.preferences), file, indent=4, ensure_ascii=False)
		except Exception:
			self.logger.exception('Failed to save preference file')

	def get_default_preference(self) -> PreferenceItem:
		return PreferenceItem(
			language=self.mcdr_server.get_language(),
		)

	@classmethod
	def __get_name(cls, obj: PreferenceSource, *, strict_type_check: bool = False) -> Optional[str]:
		if isinstance(obj, str):
			player_name = obj
		elif isinstance(obj, PlayerCommandSource):
			player_name = obj.player
		elif isinstance(obj, ConsoleCommandSource):
			player_name = CONSOLE_ALIAS
		else:
			player_name = None
			if strict_type_check:
				raise InvalidPreferenceSource('Unsupported object type during preference querying: {}'.format(type(obj)))
		return player_name

	def get_preference(self, obj: PreferenceSource, *, auto_add: bool = False, strict_type_check: bool = False) -> PreferenceItem:
		name = self.__get_name(obj, strict_type_check=strict_type_check)
		pref: Optional[PreferenceItem] = self.preferences.get(name) if name is not None else None
		if pref is None:
			pref = self.get_default_preference()
			if auto_add and name is not None:
				self.preferences[name] = pref
				self.__save_preferences()
		else:
			pref = pref.copy()
		return pref

	def get_console_preference(self) -> PreferenceItem:
		return self.get_preference(CONSOLE_ALIAS, strict_type_check=True)

	def set_preference(self, obj: PreferenceSource, pref: PreferenceItem):
		name: str = self.__get_name(obj)
		self.preferences[name] = pref.copy()
		self.__save_preferences()

	def get_preferred_language(self, obj: PreferenceSource) -> str:
		pref = self.get_preference(obj)
		if pref is not None:
			return pref.language
		return self.mcdr_server.translation_manager.language
