"""
MCDR config file stuffs
"""
import os
from logging import Logger

import ruamel.yaml as yaml
from ruamel.yaml.comments import CommentedMap

from mcdreforged.utils import resources_util
from mcdreforged.utils.lazy_item import LazyItem


class YamlDataStorage:
	def __init__(self, logger: Logger, file_path: str, default_file_path: str):
		self.logger = logger
		self.file_path = file_path
		self.default_file_path = default_file_path
		self.data = CommentedMap()
		self.default_data = LazyItem(lambda: resources_util.get_yaml(self.default_file_path))
		self.__has_changes = False

	def _load_data(self, allowed_missing_file) -> bool:
		"""
		:param bool allowed_missing_file: If set to True, missing data file will result in a FileNotFoundError(),
		otherwise it will treat it as an empty config gile
		:return: if there is any missing data entry
		:raise: FileNotFoundError
		"""
		if os.path.isfile(self.file_path):
			with open(self.file_path, encoding='utf8') as file:
				users_data = yaml.round_trip_load(file)
		else:
			if not allowed_missing_file:
				raise FileNotFoundError()
			users_data = {}
		self.__has_changes = False
		self.data = self.__fix(self.default_data.get(), users_data)
		self.save()
		return self.__has_changes

	def __fix(self, current_data: CommentedMap, users_data: CommentedMap, key_path='') -> CommentedMap:
		if not isinstance(users_data, dict):
			self.__has_changes = True
			return current_data
		else:
			current_data = current_data.copy()
			divider = ' -> ' if len(key_path) > 0 else ''
			for key in current_data.keys():
				current_key_path = key_path + divider + key
				if key in users_data:
					# if key presents in user's data
					if isinstance(current_data[key], dict):
						# dive deeper
						current_data[key] = self.__fix(current_data[key], users_data[key], current_key_path)
					else:
						# use the value in user's data
						current_data[key] = users_data[key]
				else:
					# missing config key
					self.__has_changes = True
					self.logger.warning('Option "{}" missing, use default value "{}"'.format(current_key_path, current_data[key]))
			return current_data

	def _pre_save(self, data: CommentedMap):
		pass

	def __save(self, data: CommentedMap):
		self._pre_save(data)
		with open(self.file_path, 'w', encoding='utf8') as file:
			yaml.round_trip_dump(data, file)

	def save(self):
		self.__save(self.data)

	def save_default(self):
		self.__save(self.default_data.get())

	def __getitem__(self, item):
		return self.data[item]

	# -------------------------
	#   Actual data analyzers
	# -------------------------

	def is_debug_on(self):
		for value in self.data['debug']:
			if value is True:
				return True
		return False


CONFIG_FILE = 'config.yml'
DEFAULT_CONFIG_RESOURCE_PATH = 'resources/default_config.yml'


class Config(YamlDataStorage):
	def __init__(self, logger: Logger):
		super().__init__(logger, CONFIG_FILE, DEFAULT_CONFIG_RESOURCE_PATH)
		self.storage = ()

	def read_config(self, allowed_missing_file):
		return self._load_data(allowed_missing_file)
