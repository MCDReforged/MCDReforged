"""
Permission control things
"""
from typing import Set, Any, List

from typing_extensions import override

from mcdreforged.command.command_source import CommandSource
from mcdreforged.info_reactor.info import *
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.permission.permission_level import PermissionLevel, PermissionLevelItem, PermissionParam
from mcdreforged.utils import collection_utils
from mcdreforged.utils.yaml_data_storage import YamlDataStorage

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


DEFAULT_PERMISSION_RESOURCE_PATH = 'resources/default_permission.yml'


class PermissionStorage(YamlDataStorage):
	# Enable item setting via []
	def __setitem__(self, key: str, value: Any):
		self._data[key] = value

	@override
	def _pre_save(self, data: dict):
		# Deduplicate the permission data
		for key, value in data.items():
			if key in PermissionLevel.NAMES and isinstance(value, list):
				data[key] = collection_utils.unique_list(data[key])
		# Change empty list to None for nicer look in the .yml file
		for key, value in data.items():
			if key in PermissionLevel.NAMES and value is not None and len(value) == 0:
				data[key] = None


class PermissionManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer', permission_file_path: str):
		self.mcdr_server = mcdr_server
		self.storage = PermissionStorage(mcdr_server.logger, permission_file_path, DEFAULT_PERMISSION_RESOURCE_PATH)
		self.__tr = mcdr_server.create_internal_translator('permission_manager').tr

	# --------------
	# File Operating
	# --------------

	def load_permission_file(self, *, allowed_missing_file: bool = True):
		"""
		Load the permission file from disk
		"""
		self.storage.read_config(allowed_missing_file)

	def file_presents(self) -> bool:
		return self.storage.file_presents()

	def save_default(self):
		self.storage.save_default()

	# ---------------------
	# Permission processing
	# ---------------------

	def get_default_permission_level(self) -> str:
		"""
		Return the default permission level
		"""
		return self.storage['default_level']

	def set_default_permission_level(self, level: PermissionLevelItem):
		"""
		Set default permission level
		A message will be informed using server logger
		"""
		self.storage['default_level'] = level.name
		self.storage.save()
		self.mcdr_server.logger.info(self.__tr('set_default_permission_level.done', level.name))

	def get_permission_group_list(self, value: PermissionParam) -> List[str]:
		"""
		Return the list of the player who has permission level <level>
		Example return value: ['Steve', 'Alex']

		:param value: a permission related object
		"""
		level_name = PermissionLevel.from_value(value).name
		if self.storage[level_name] is None:
			self.storage[level_name] = []
		return self.storage[level_name]

	def add_player(self, player: str, level_name: Optional[str] = None) -> int:
		"""
		Add a new player with permission level level_name
		If level_name is not set use default level
		Then save the permission data to file

		:param player: the name of the player
		:param level_name: the permission level name
		:return: the permission of the player after operation done
		"""
		if level_name is None:
			level_name = self.get_default_permission_level()
		PermissionLevel.from_value(level_name)  # validity check
		self.get_permission_group_list(level_name).append(player)
		self.mcdr_server.logger.mdebug('Added player {} with permission level {}'.format(player, level_name), option=DebugOption.PERMISSION)
		self.storage.save()
		return PermissionLevel.from_value(level_name).level

	def remove_player(self, player: str):
		"""
		Remove a player from data, then save the permission data to file
		If the player has multiple permission level, remove them all
		And then save the permission data to file

		:param player: the name of the player
		"""
		while True:
			level = self.get_player_permission_level(player, auto_add=False)
			if level is None:
				break
			self.get_permission_group_list(level).remove(player)
		self.mcdr_server.logger.mdebug('Removed player {}'.format(player), option=DebugOption.PERMISSION)
		self.storage.save()

	def set_permission_level(self, player: str, new_level: PermissionLevelItem):
		"""
		Set new permission level of the player
		Basically it will remove the player first, then add the player with given permission level
		Then save the permission data to file

		:param player: the name of the player
		:param new_level: the permission level name
		"""
		self.remove_player(player)
		self.add_player(player, new_level.name)
		self.mcdr_server.logger.info(self.__tr('set_permission_level.done', player, new_level.name))

	def touch_player(self, player: str):
		"""
		Add player if it's not in permission data

		:param player: the name of the player
		"""
		self.get_player_permission_level(player)

	def get_player_permission_level(self, player: str, *, auto_add: bool = True) -> Optional[int]:
		"""
		If the player is not in the permission data set its level to default_level,
		unless parameter auto_add is set to False, then it will return None
		If the player is in multiple permission level group it will return the highest one

		:param player: the name of the player
		:param auto_add: if it's True when player is invalid he will receive the default permission level
		:return the permission level from a player's name. If auto_add is False and player invalid return None
		"""
		for level_value in PermissionLevel.LEVELS[::-1]:  # high -> low
			if player in self.get_permission_group_list(level_value):
				return level_value
		else:
			if auto_add:
				return self.add_player(player)
			else:
				return None

	def get_permission(self, source: CommandSource) -> int:
		"""
		Gets called in CommandSource implementation
		"""
		if isinstance(source, ConsoleCommandSource):
			return PermissionLevel.CONSOLE_LEVEL
		elif isinstance(source, PlayerCommandSource):
			return self.get_player_permission_level(source.player)
		else:
			raise TypeError('Unknown type {} in get_permission'.format(type(source)))

	def get_players(self) -> Set[str]:
		players = set()
		for level_value in PermissionLevel.LEVELS:
			players.update(self.get_permission_group_list(level_value))
		return players
