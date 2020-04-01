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
	LEVEL_VALUE = collections.OrderedDict([
		('admin', ADMIN),
		('helper', HELPER),
		('user', USER),
		('guest', GUEST)
	])
	LEVEL_NAME = collections.OrderedDict([(value, item) for item, value in LEVEL_VALUE.items()])
	TOP_LEVEL = list(LEVEL_VALUE.items())[0][1]


class PermissionManager:
	def __init__(self, server, permission_file):
		self.server = server
		self.permission_file = permission_file
		self.data = None
		self.load()

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

	# deduplicate the permission data
	def unique(self):
		for key, value in self.data.items():
			if key in PermissionLevel.LEVEL_VALUE.keys() and type(value) is list:
				self.data[key] = tool.unique_list(self.data[key])
		self.save()

	# change empty list to None for nicer look in the .yml
	def empty_to_none(self):
		for key, value in self.data.items():
			if key in PermissionLevel.LEVEL_VALUE.keys() and value is not None and len(value) == 0:
				self.data[key] = None

	def save(self):
		self.empty_to_none()
		with open(self.permission_file, 'w') as file:
			yaml.round_trip_dump(self.data, file)

	def get_permission_group_list(self, name):
		if type(name) == int:
			name = PermissionLevel.LEVEL_NAME[name]
		if self.data[name] is None:
			self.data[name] = []
		return self.data[name]

	# add a new player
	def add_player(self, player):
		level_name = self.data['default_level']
		self.get_permission_group_list(level_name).append(player)
		self.save()
		self.server.logger.info('Added player {} with permission level {}'.format(player, level_name))
		return PermissionLevel.LEVEL_VALUE[level_name]

	# set new permission level of the player
	def set_level(self, player, new_level):
		old_level = self.get_player_level(player)
		old_level_name = PermissionLevel.LEVEL_NAME[old_level]
		new_level_name = PermissionLevel.LEVEL_NAME[new_level]
		self.get_permission_group_list(old_level_name).remove(player)
		self.get_permission_group_list(new_level_name).append(player)
		self.unique()  # includes self.save()
		self.server.logger.info('The permission level of {} has changed from {} to {}'.format(player, old_level_name, new_level_name))

	# return the permission level from a player's name
	# if the player is not in the permission data set its level to default_level
	# if the player is in multiple permission level group it will return the highest one
	def get_player_level(self, name):
		for level_value in PermissionLevel.LEVEL_VALUE.values():
			if name in self.get_permission_group_list(level_value):
				return level_value
		else:
			return self.add_player(name)

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
