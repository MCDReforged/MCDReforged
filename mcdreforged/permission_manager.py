"""
Permission control things
"""

import collections
from typing import List, Dict, Optional, Any

from mcdreforged.config import YamlDataStorage
from mcdreforged.info import *
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import DebugOption


class PermissionLevelItem:
	def __init__(self, name: str, level: int):
		self.name = name
		self.level = level

	def __str__(self):
		return 'Permission[name={},level={}]'.format(self.name, self.level)

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.level < other.level


class _PermissionLevelStorage:
	STORAGE = []  # type: List[PermissionLevelItem]

	@classmethod
	def register(cls, item: PermissionLevelItem):
		cls.STORAGE.append(item)
		cls.STORAGE.sort()
		return item.level

	@classmethod
	def get_value_dict(cls):
		return collections.OrderedDict([(item.name, item.level) for item in cls.STORAGE])


class PermissionLevel:
	GUEST	= _PermissionLevelStorage.register(PermissionLevelItem('guest', 0))
	USER	= _PermissionLevelStorage.register(PermissionLevelItem('user', 1))
	HELPER	= _PermissionLevelStorage.register(PermissionLevelItem('helper', 2))
	ADMIN	= _PermissionLevelStorage.register(PermissionLevelItem('admin', 3))
	OWNER	= _PermissionLevelStorage.register(PermissionLevelItem('owner', 4))
	__NAME_DICT = collections.OrderedDict([(item.name, item) for item in _PermissionLevelStorage.STORAGE])  # type: Dict[str, PermissionLevelItem]
	__LEVEL_DICT = collections.OrderedDict([(item.level, item) for item in _PermissionLevelStorage.STORAGE])  # type: Dict[int, PermissionLevelItem]
	LEVELS = [item.level for item in _PermissionLevelStorage.STORAGE]
	NAMES = [item.name for item in _PermissionLevelStorage.STORAGE]
	INSTANCES = _PermissionLevelStorage.STORAGE.copy()

	MAXIMUM_LEVEL = LEVELS[-1]
	MINIMUM_LEVEL = LEVELS[0]
	MCDR_CONTROL_LEVEL = ADMIN
	PHYSICAL_SERVER_CONTROL_LEVEL = OWNER
	CONSOLE_LEVEL = MAXIMUM_LEVEL

	@classmethod
	def __check_range(cls, level: int):
		if cls.MINIMUM_LEVEL <= level <= cls.MAXIMUM_LEVEL:
			pass
		else:
			raise ValueError('Value {} out of range [{}, {}]'.format(level, cls.MINIMUM_LEVEL, cls.MAXIMUM_LEVEL))

	@classmethod
	def from_value(cls, value):
		"""
		Convert any type of permission level into int value. Examples:
			'guest'	-> 0
			'admin'	-> 3
			'1'		-> 1
			2		-> 2
		If the argument is invalid return None

		:param value: a permission related object
		:type value: str or int
		:rtype: PermissionLevelItem
		"""
		level = None
		if isinstance(value, str):
			if value.isdigit():
				value = int(value)
			elif value in cls.NAMES:
				level = cls.__NAME_DICT[value]
		if isinstance(value, int):
			cls.__check_range(value)
			level = cls.__LEVEL_DICT[value]
		if level is None:
			raise TypeError('Unsupported value for {}: {}'.format(cls.__name__, value))
		return level

	@classmethod
	def get_level(cls, value) -> Optional[PermissionLevelItem]:
		"""
		Fail-proof version of from_value
		"""
		try:
			return cls.from_value(value)
		except (TypeError, ValueError):
			return None


PERMISSION_FILE = 'permission.yml'
DEFAULT_PERMISSION_RESOURCE_PATH = 'resources/default_permission.yml'


class PermissionManager(YamlDataStorage):
	def __init__(self, mcdr_server):
		super().__init__(mcdr_server.logger, PERMISSION_FILE, DEFAULT_PERMISSION_RESOURCE_PATH)
		self.mcdr_server = mcdr_server
		self.data = {}  # type: Dict[str, Any]

	# --------------
	# File Operating
	# --------------

	def load_permission_file(self, *, allowed_missing_file=True):
		"""
		Load the permission file from disk
		"""
		self._load_data(allowed_missing_file)

	def _pre_save(self, data):
		# Deduplicate the permission data=
		for key, value in self.data.items():
			if key in PermissionLevel.NAMES and isinstance(value, list):
				self.data[key] = misc_util.unique_list(self.data[key])
		# Change empty list to None for nicer look in the .yml file
		for key, value in self.data.items():
			if key in PermissionLevel.NAMES and value is not None and len(value) == 0:
				self.data[key] = None

	# ---------------------
	# Permission processing
	# ---------------------

	def get_default_permission_level(self):
		"""
		Return the default permission level
		:rtype: str
		"""
		return self.data['default_level']

	def set_default_permission_level(self, level: PermissionLevelItem):
		"""
		Set default permission level
		A message will be informed using server logger
		"""
		self.data['default_level'] = level.name
		self.save()
		self.mcdr_server.logger.info(self.mcdr_server.tr('permission_manager.set_default_permission_level.done', level.name))

	def get_permission_group_list(self, value):
		"""
		Return the list of the player who has permission level <level>
		Example return value: ['Steve', 'Alex']

		:param str or int value: a permission related object
		:rtype: list[str]
		"""
		level_name = PermissionLevel.from_value(value).name
		if self.data[level_name] is None:
			self.data[level_name] = []
		return self.data[level_name]

	def add_player(self, player, level_name=None):
		"""
		Add a new player with permission level level_name
		If level_name is not set use default level
		Then save the permission data to file

		:param str player: the name of the player
		:param str level_name: the permission level name
		:return: the permission of the player after operation done
		:rtype: int
		"""
		if level_name is None:
			level_name = self.get_default_permission_level()
		PermissionLevel.from_value(level_name)  # validity check
		self.get_permission_group_list(level_name).append(player)
		self.mcdr_server.logger.debug('Added player {} with permission level {}'.format(player, level_name), option=DebugOption.PERMISSION)
		self.save()
		return PermissionLevel.from_value(level_name).level

	def remove_player(self, player):
		"""
		Remove a player from data, then save the permission data to file
		If the player has multiple permission level, remove them all
		And then save the permission data to file

		:param str player: the name of the player
		"""
		while True:
			level = self.get_player_permission_level(player, auto_add=False)
			if level is None:
				break
			self.get_permission_group_list(level).remove(player)
		self.mcdr_server.logger.debug('Removed player {}'.format(player), option=DebugOption.PERMISSION)
		self.save()

	def set_permission_level(self, player, new_level):
		"""
		Set new permission level of the player
		Basically it will remove the player first, then add the player with given permission level
		Then save the permission data to file

		:param str player: the name of the player
		:param PermissionLevelItem new_level: the permission level name
		"""
		self.remove_player(player)
		self.add_player(player, new_level.name)
		self.mcdr_server.logger.info(self.mcdr_server.tr('permission_manager.set_permission_level.done', player, new_level.name))

	def touch_player(self, player):
		"""
		Add player if it's not in permission data

		:param str player: the name of the player
		"""
		self.get_player_permission_level(player)

	def get_player_permission_level(self, player, auto_add=True):
		"""
		If the player is not in the permission data set its level to default_level,
		unless parameter auto_add is set to False, then it will return None
		If the player is in multiple permission level group it will return the highest one

		:param str player: the name of the player
		:param bool auto_add: if it's True when player is invalid he will receive the default permission level
		:return the permission level from a player's name. If auto_add is False and player invalid return None
		:rtype: int or None
		"""
		for level_value in PermissionLevel.LEVELS:
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
