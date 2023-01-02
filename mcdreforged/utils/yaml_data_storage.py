import os
from logging import Logger
from threading import RLock
from typing import Tuple

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

from mcdreforged.utils import resources_util, misc_util, file_util
from mcdreforged.utils.lazy_item import LazyItem


class YamlDataStorage:
	def __init__(self, logger: Logger, file_path: str, default_file_path: str):
		self._logger = logger
		self.__file_path = file_path
		self.__default_file_path = default_file_path
		self.__default_data = LazyItem(lambda: resources_util.get_yaml(self.__default_file_path))
		self._data = CommentedMap()
		self._data_operation_lock = RLock()

	def __getitem__(self, option: str):
		return self._data[option]

	def to_dict(self) -> dict:
		with self._data_operation_lock:
			return misc_util.deep_copy_dict(self._data)

	def file_presents(self) -> bool:
		return os.path.isfile(self.__file_path)

	def read_config(self, allowed_missing_file: bool):
		"""
		:param bool allowed_missing_file: If set to True, missing data file will result in a FileNotFoundError(),
		otherwise it will treat it as an empty config file
		:return: if there is any missing data entry
		:raise: FileNotFoundError
		"""
		if self.file_presents():
			with open(self.__file_path, encoding='utf8') as file:
				users_data = YAML().load(file)
		else:
			if not allowed_missing_file:
				raise FileNotFoundError()
			users_data = {}
		fixed_result, has_missing = self.__fix(dict(self.__default_data.get()), users_data)
		with self._data_operation_lock:
			self._data = fixed_result
		if has_missing:
			self.save()
		return has_missing

	def __fix(self, current_data: dict, users_data: CommentedMap, key_path='') -> Tuple[dict, bool]:
		"""
		:return: pair of (fixed result, has missing)
		"""
		if not isinstance(users_data, dict):
			return current_data, True
		else:
			result = users_data.copy()
			has_missing = False
			divider = ' -> ' if len(key_path) > 0 else ''
			for key in current_data.keys():
				current_key_path = key_path + divider + key
				if key in users_data:
					# if key presents in user's data
					if isinstance(current_data[key], dict):
						# dive deeper
						result[key], missing = self.__fix(current_data[key], users_data[key], current_key_path)
						has_missing |= missing
					else:
						# use the value in user's data
						result[key] = users_data[key]
				else:
					# missing config key
					result[key] = current_data[key]
					has_missing = True
					self._logger.warning('Option "{}" missing, use default value "{}"'.format(current_key_path, current_data[key]))
			return result, has_missing

	def _pre_save(self, data: CommentedMap):
		pass

	def __save(self, data: CommentedMap):
		self._pre_save(data)
		with file_util.safe_write(self.__file_path, encoding='utf8') as file:
			YAML().dump(data, file)

	def save(self):
		with self._data_operation_lock:
			self.__save(self._data)

	def get_default_yaml(self):
		return self.__default_data.get()

	def save_default(self):
		self.__save(self.get_default_yaml())
