"""
Permission control things
"""

import collections

import ruamel.yaml as yaml
from ruamel.yaml.comments import CommentedSeq

from mcdr.command.command_source import CommandSource
from mcdr.info import *
from mcdr.utils import misc_util


class PermissionLevel:
	OWNER = 4
	ADMIN = 3
	HELPER = 2
	USER = 1
	GUEST = 0
	DICT_VALUE = collections.OrderedDict([
		('owner', OWNER),
		('admin', ADMIN),
		('helper', HELPER),
		('user', USER),
		('guest', GUEST)
	])
	DICT_NAME = collections.OrderedDict([(value, item) for item, value in DICT_VALUE.items()])
	VALUE = list(DICT_VALUE.values())
	NAME = list(DICT_VALUE.keys())

	TOP_LEVEL = VALUE[0]
	BOTTOM_LEVEL = VALUE[-1]
	MCDR_CONTROL_LEVEL = ADMIN


class PermissionManager:
	def __init__(self, mcdr_server, permission_file):
		self.mcdr_server = mcdr_server
		self.permission_file = permission_file
		self.data = None

	# --------------
	# File Operating
	# --------------

	def load_permission_file(self):
		"""
		Load the permission file from disk
		"""
		try:
			with open(self.permission_file, encoding='utf8') as file:
				self.data = yaml.round_trip_load(file)
		except:
			self.mcdr_server.logger.warning(self.mcdr_server.tr('permission_manager.load.fail', self.permission_file))
			self.data = {
				'default_level': 'user',
				'owner': None,
				'admin': None,
				'helper': None,
				'user': None,
				'guest': None
			}
		for name in PermissionLevel.NAME:
			if name not in self.data:
				self.data[name] = None
		self.save()

	def deduplicate_data(self):
		"""
		Deduplicate the permission data=
		"""
		for key, value in self.data.items():
			if key in PermissionLevel.NAME and type(value) in [list, CommentedSeq]:
				self.data[key] = misc_util.unique_list(self.data[key])

	def empty_to_none(self):
		"""
		Change empty list to None for nicer look in the .yml file
		"""
		for key, value in self.data.items():
			if key in PermissionLevel.NAME and value is not None and len(value) == 0:
				self.data[key] = None

	def save(self):
		"""
		Save data to file
		"""
		self.deduplicate_data()
		self.empty_to_none()
		with open(self.permission_file, 'w', encoding='utf8') as file:
			yaml.round_trip_dump(self.data, file)

	# ---------------------
	# Permission processing
	# ---------------------

	@staticmethod
	def format_level_value(level):
		"""
		Convert any type of permission level into int value. Examples:
			'guest'	-> 0
			'admin'	-> 3
			'1'		-> 1
			2		-> 2
		If the argument is invalid return None

		:param level: a permission related object
		:type level: str or int
		:rtype: int or None
		"""
		if type(level) == str:
			if level.isdigit():
				level = int(level)
			elif level in PermissionLevel.NAME:
				level = PermissionLevel.DICT_VALUE[level]
		if type(level) is int and PermissionLevel.BOTTOM_LEVEL <= level <= PermissionLevel.TOP_LEVEL:
			return level
		return None

	@staticmethod
	def format_level_name(level):
		"""
		Convert any type of permission level into str. Examples:
			0		-> 'guest'
			'1'		-> 'user'
			'admin'	-> 'admin'
		If the argument is invalid return None

		:param level: a permission related object
		:type level: str or int
		:rtype: str or None
		"""
		value = PermissionManager.format_level_value(level)
		if value is None:
			return value
		return PermissionLevel.DICT_NAME[value]

	def get_default_permission_level(self):
		"""
		Return the default permission level

		:rtype: str
		"""
		return self.data['default_level']

	def set_default_permission_level(self, level):
		"""
		Set default permission level
		A message will be informed using server logger

		:param level: a permission related object
		:type level: str or int
		"""
		level = self.format_level_name(level)
		self.data['default_level'] = level
		self.save()
		self.mcdr_server.logger.info(
			self.mcdr_server.tr('permission_manager.set_default_permission_level.done', self.format_level_name(level)))

	def get_permission_group_list(self, level):
		"""
		Return the list of the player who has permission level <level>
		Example return value: ['Steve', 'Alex']

		:param level: a permission related object
		:type level: str or int
		:rtype: list[str]
		"""
		name = self.format_level_name(level)
		if name is None:
			raise TypeError('{} is not a valid permission level'.format(level))
		if self.data[name] is None:
			self.data[name] = []
		return self.data[name]

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
		self.get_permission_group_list(level_name).append(player)
		self.mcdr_server.logger.debug('Added player {} with permission level {}'.format(player, level_name))
		self.save()
		return self.format_level_value(level_name)

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
		self.mcdr_server.logger.debug('Removed player {}'.format(player))
		self.save()

	def set_permission_level(self, player, new_level):
		"""
		Set new permission level of the player
		Basically it will remove the player first, then add the player with given permission level
		Then save the permission data to file

		:param str player: the name of the player
		:param str new_level: the permission level name
		"""
		self.remove_player(player)
		self.add_player(player, new_level)
		self.mcdr_server.logger.info(
			self.mcdr_server.tr('permission_manager.set_permission_level.done', player, self.format_level_name(new_level)))

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
		for level_value in PermissionLevel.VALUE:
			if player in self.get_permission_group_list(level_value):
				return level_value
		else:
			if auto_add:
				return self.add_player(player)
			else:
				return None

	def get_info_permission_level(self, info):
		"""
		Return the permission level from a info instance, return None if it's the info is not from a user
		Console input always has the top level

		:type info: Info or str
		:rtype: int or None
		"""
		if info.source == InfoSource.CONSOLE:
			return PermissionLevel.TOP_LEVEL
		elif info.is_player:
			return self.get_player_permission_level(info.player)
		else:
			return None

	def has_permission(self, source: CommandSource, level: int):
		if source.source == InfoSource.CONSOLE:
			return PermissionLevel.TOP_LEVEL
		elif info.is_player:
			return self.get_player_permission_level(info.player)
		else:
			return None