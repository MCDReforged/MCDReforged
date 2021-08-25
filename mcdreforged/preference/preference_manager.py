import json
import os
from typing import Optional, Dict, TYPE_CHECKING, Union

from mcdreforged.command.command_source import CommandSource, PlayerCommandSource, ConsoleCommandSource
from mcdreforged.constants import core_constant, plugin_constant
from mcdreforged.utils.serializer import Serializable, deserialize, serialize

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


PREFERENCE_FILE = os.path.join(plugin_constant.PLUGIN_CONFIG_DIRECTORY, core_constant.PACKAGE_NAME, 'preferences.json')
CONSOLE_ALIAS = '#@MCDR_Console@#'


class PreferenceItem(Serializable):
	language: Optional[str]


PreferenceStorage = Dict[str, PreferenceItem]


class PreferenceManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server: 'MCDReforgedServer' = mcdr_server
		self.logger = mcdr_server.logger
		self.preferences: PreferenceStorage = {}

	def load_preferences(self):
		try:
			with open(PREFERENCE_FILE, 'r', encoding='utf8') as file:
				self.preferences = deserialize(json.load(file), PreferenceStorage, error_at_missing=True, error_at_redundancy=True)
		except Exception as e:
			if not isinstance(e, FileNotFoundError):
				self.logger.exception('Failed to load preference file')
			self.preferences = {}
			self.save_preferences()

	def save_preferences(self):
		try:
			dir_path = os.path.dirname(PREFERENCE_FILE)
			if not os.path.isdir(dir_path):
				os.makedirs(dir_path)
			with open(PREFERENCE_FILE, 'w', encoding='utf8') as file:
				json.dump(serialize(self.preferences), file, indent=4, ensure_ascii=False)
		except:
			self.logger.exception('Failed to save preference file')

	def get_default_preference(self) -> PreferenceItem:
		return PreferenceItem(
			language=self.mcdr_server.get_language()
		)

	def get_preference(self, obj: Union[str, CommandSource], *, auto_add: bool = False, strict_type_check: bool = False) -> PreferenceItem:
		if isinstance(obj, str):
			player_name = obj
		elif isinstance(obj, PlayerCommandSource):
			player_name = obj.player
		elif isinstance(obj, ConsoleCommandSource):
			player_name = CONSOLE_ALIAS
		else:
			player_name = None
			if strict_type_check:
				raise TypeError('Unsupported object type during preference querying: {}'.format(type(obj)))
		pref = self.preferences.get(player_name)
		if pref is None:
			pref = self.get_default_preference()
			if auto_add and player_name is not None:
				self.preferences[player_name] = pref
				self.save_preferences()
		return pref

	def get_preferred_language(self, obj: Union[str, CommandSource]) -> str:
		pref = self.get_preference(obj)
		if pref is not None:
			return pref.language
		return self.mcdr_server.translation_manager.language


