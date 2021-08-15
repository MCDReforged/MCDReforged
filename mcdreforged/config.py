"""
MCDR config file stuffs
"""
from logging import Logger
from typing import Any

from mcdreforged.utils.yaml_data_storage import YamlDataStorage

CONFIG_FILE = 'config.yml'
DEFAULT_CONFIG_RESOURCE_PATH = 'resources/default_config.yml'


class Config(YamlDataStorage):
	def __init__(self, logger: Logger):
		super().__init__(logger, CONFIG_FILE, DEFAULT_CONFIG_RESOURCE_PATH)

	def read_config(self, allowed_missing_file):
		return self._load_data(allowed_missing_file)

	def __getitem__(self, option: str):
		return self._data[option]

	def set_value(self, option: str, value: Any):
		if option in self._data and type(self[option]) == type(value):
			self._data[option] = value
		elif option not in self._data:
			raise KeyError('Cannot set option {} since the config does not contains it'.format(option))
		else:
			raise ValueError('Cannot set option {} in type {} to value {} in type {}'.format(option, type(self[option]), value, type(value)))

	# -------------------------
	#   Actual data analyzers
	# -------------------------

	def is_debug_on(self):
		for value in self._data['debug']:
			if value is True:
				return True
		return False
