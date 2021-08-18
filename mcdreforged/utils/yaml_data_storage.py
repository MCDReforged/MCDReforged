import os
from logging import Logger
from threading import RLock

from ruamel import yaml
from ruamel.yaml.comments import CommentedMap

from mcdreforged.utils import resources_util
from mcdreforged.utils.lazy_item import LazyItem


class YamlDataStorage:
	def __init__(self, logger: Logger, file_path: str, default_file_path: str):
		self.logger = logger
		self.__file_path = file_path
		self.__default_file_path = default_file_path
		self._data = CommentedMap()
		self.__default_data = LazyItem(lambda: resources_util.get_yaml(self.__default_file_path))
		self.__has_changes = False
		self._data_operation_lock = RLock()

	def to_dict(self) -> dict:
		def process(data: dict) -> dict:
			ret = {}
			for key, value in data.items():
				if isinstance(value, dict):
					value = process(value)
				ret[key] = value
			return ret
		return process(self._data)

	def file_presents(self) -> bool:
		return os.path.isfile(self.__file_path)

	def _load_data(self, allowed_missing_file) -> bool:
		"""
		:param bool allowed_missing_file: If set to True, missing data file will result in a FileNotFoundError(),
		otherwise it will treat it as an empty config gile
		:return: if there is any missing data entry
		:raise: FileNotFoundError
		"""
		if self.file_presents():
			with open(self.__file_path, encoding='utf8') as file:
				users_data = yaml.round_trip_load(file)
		else:
			if not allowed_missing_file:
				raise FileNotFoundError()
			users_data = {}
		self.__has_changes = False
		fixed_result = self.__fix(dict(self.__default_data.get()), users_data)
		with self._data_operation_lock:
			self._data = fixed_result
		if self.__has_changes:
			self.save()
		return self.__has_changes

	def __fix(self, current_data: dict, users_data: CommentedMap, key_path='') -> dict:
		if not isinstance(users_data, dict):
			self.__has_changes = True
			return current_data
		else:
			result = users_data.copy()
			divider = ' -> ' if len(key_path) > 0 else ''
			for key in current_data.keys():
				current_key_path = key_path + divider + key
				if key in users_data:
					# if key presents in user's data
					if isinstance(current_data[key], dict):
						# dive deeper
						result[key] = self.__fix(current_data[key], users_data[key], current_key_path)
					else:
						# use the value in user's data
						result[key] = users_data[key]
				else:
					# missing config key
					result[key] = current_data[key]
					self.__has_changes = True
					self.logger.warning('Option "{}" missing, use default value "{}"'.format(current_key_path, current_data[key]))
			return result

	def _pre_save(self, data: CommentedMap):
		pass

	def __save(self, data: CommentedMap):
		with self._data_operation_lock:
			self._pre_save(data)
			with open(self.__file_path, 'w', encoding='utf8') as file:
				yaml.round_trip_dump(data, file, width=4096)  # specifying width=4096 to prevent yaml breaks long string into multiple lines

	def save(self):
		self.__save(self._data)

	def get_default_yaml(self):
		return self.__default_data.get()

	def save_default(self):
		self.__save(self.get_default_yaml())
