import os
from logging import Logger
from threading import RLock
from typing import Tuple

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq
from ruamel.yaml.scalarbool import ScalarBoolean

from mcdreforged.utils import resources_utils, file_utils
from mcdreforged.utils.lazy_item import LazyItem


def transform_yaml_to_dict(source: dict) -> dict:
	ret = {}
	for key, value in source.items():
		if isinstance(value, dict):
			value = transform_yaml_to_dict(value)
		elif isinstance(value, ScalarBoolean):  # ScalarBoolean uses int as the base class
			value = bool(value)
		else:
			for cls in [bool, int, float, str, list]:
				if isinstance(value, cls):
					value = cls(value)
					break
		ret[key] = value
	return ret


class YamlDataStorage:
	def __init__(self, logger: Logger, file_path: str, default_file_path: str):
		self._logger = logger
		self.__file_path = file_path
		self.__default_file_path = default_file_path
		self.__default_data = LazyItem(lambda: resources_utils.get_yaml(self.__default_file_path))
		self._data = CommentedMap()
		self._data_operation_lock = RLock()

	def __getitem__(self, option: str):
		return self._data[option]

	def to_dict(self) -> dict:
		with self._data_operation_lock:
			return transform_yaml_to_dict(self._data)

	def file_presents(self) -> bool:
		return os.path.isfile(self.__file_path)

	def read_config(self, allowed_missing_file: bool, save_on_missing: bool = True):
		"""
		:param bool allowed_missing_file: If set to True, missing data file will result in a FileNotFoundError(),
		otherwise it will treat it as an empty config file
		:param bool save_on_missing: Perform save() on missing
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
		if has_missing and save_on_missing:
			self.save()
		return has_missing

	def __fix(self, current_data: dict, users_data: CommentedMap, key_path: str = '') -> Tuple[dict, bool]:
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
		file_utils.safe_write_yaml(self.__file_path, data)

	def save(self):
		with self._data_operation_lock:
			self.__save(self._data)

	def get_default_yaml(self) -> CommentedMap:
		return self.__default_data.get()

	def save_default(self):
		self.__save(self.get_default_yaml())

	@classmethod
	def merge_dict(cls, src: dict, dst: dict):
		"""
		Does not add new keys
		"""
		for key, value in src.items():
			old_value = dst.get(key)
			if isinstance(value, dict) and isinstance(old_value, dict):
				cls.merge_dict(value, old_value)
			else:
				if key in dst and old_value != value:
					if isinstance(old_value, CommentedSeq):
						# the comment of the last seq item belongs to the next element. keep it
						ca_items: dict = old_value.ca.items
						last_comment = ca_items.get(len(old_value) - 1)
						# cannot use clear(), cuz that uses pop(-1) and will mess up the comment index
						while old_value:
							old_value.pop(len(old_value) - 1)
						old_value.extend(value)
						old_value.ca.items[len(old_value) - 1] = last_comment
					else:
						dst[key] = value

	def merge_from_dict(self, data: dict):
		self.merge_dict(data, self._data)
