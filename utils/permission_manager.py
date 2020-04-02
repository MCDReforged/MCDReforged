# -*- coding: utf-8 -*-
import collections
import copy
import ruamel.yaml as yaml
from utils import tool
from utils.info import InfoSource


class PermissionLevel:
	ADMIN = 3
	HELPER = 2
	USER = 1
	GUEST = 0
	DICT_VALUE = collections.OrderedDict([
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


class PermissionManager:
	def __init__(self, server, permission_file):
		self.server = server
		self.permission_file = permission_file
		self.data = None
		self.load()

	# File operating

	def load(self):
		try:
			with open(self.permission_file) as file:
				self.data = yaml.round_trip_load(file)
		except:
			self.server.logger.warning(f'Fail to load {self.permission_file}, using default empty data')
			self.data = None
		if self.data is None:
			self.data = {
				'default_level': 'user',
				'admin': [],
				'helper': [],
				'user': [],
				'guest': []
			}
		self.unique()
		self.save()

	# deduplicate the permission data
	def unique(self):
		for key, value in self.data.items():
			if key in PermissionLevel.VALUE and type(value) is list:
				self.data[key] = tool.unique_list(self.data[key])

	# change empty list to None for nicer look in the .yml
	def empty_to_none(self):
		for key, value in self.data.items():
			if key in PermissionLevel.NAME and value is not None and len(value) == 0:
				self.data[key] = None

	def save(self):
		self.empty_to_none()
		with open(self.permission_file, 'w') as file:
			yaml.round_trip_dump(self.data, file)

	# Permission processing

	# convert any type of permission level into int value, examples:
	# 'guest' -> 0; '1' -> 1; 'admin' -> 3
	# if the argument is invalid return None
	@staticmethod
	def format_level_value(level):
		if type(level) == str:
			if level.isdigit():
				level = int(level)
			elif level in PermissionLevel.NAME:
				level = PermissionLevel.DICT_VALUE[level]
		if type(level) is int and PermissionLevel.BOTTOM_LEVEL <= level <= PermissionLevel.TOP_LEVEL:
			return level
		return None

	# convert any type of permission level into str , examples:
	# 0 -> 'guest'; '1' -> 'user'; 'admin' -> 'admin'
	# if the argument is invalid return None
	@staticmethod
	def format_level_name(level):
		value = PermissionManager.format_level_value(level)
		if value is None:
			return value
		return PermissionLevel.DICT_NAME[value]

	# return the list of the player who has permission level <level>
	def get_permission_group_list(self, level):
		name = self.format_level_name(level)
		if name is None:
			raise TypeError(f'{str(level)} is not a valid permission level')
		if self.data[name] is None:
			self.data[name] = []
		return self.data[name]

	# add a new player
	def add_player(self, player, level_name=None):
		if level_name is None:
			level_name = self.data['default_level']
		self.get_permission_group_list(level_name).append(player)
		self.server.logger.debug('Added player {} with permission level {}'.format(player, level_name))
		self.save()
		return self.format_level_value(level_name)

	# add a new player
	def remove_player(self, player):
		while True:
			level = self.get_player_level(player, auto_add=False)
			if level is None:
				break
			self.get_permission_group_list(level).remove(player)
		self.server.logger.debug('Removed player {}'.format(player))
		self.save()

	# set new permission level of the player
	def set_level(self, player, new_level):
		self.remove_player(player)
		self.add_player(player, new_level)
		self.server.logger.info('The permission level of {} has set to {}'.format(player, self.format_level_name(new_level)))

	# return the permission level from a player's name
	# if the player is not in the permission data set its level to default_level, unless parameter auto_add is set
	# to False, then it will return None
	# if the player is in multiple permission level group it will return the highest one
	def get_player_level(self, name, auto_add=True):
		for level_value in PermissionLevel.VALUE:
			if name in self.get_permission_group_list(level_value):
				return level_value
		else:
			if auto_add:
				return self.add_player(name)
			else:
				return None

	# add player if necessary
	def touch_player(self, player):
		self.get_player_level(player)

	# return the permission level from a info instance
	# console input always has the top level
	# return None if it's the info is not from a user
	def get_info_level(self, info):
		if info.source == InfoSource.CONSOLE:
			return PermissionLevel.TOP_LEVEL
		elif info.is_player:
			return self.get_player_level(info.player)
		else:
			return None
