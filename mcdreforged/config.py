"""
MCDR config file stuffs
"""
import os

import ruamel.yaml as yaml

from mcdreforged.logger import DebugOption


class Config:
	def __init__(self, mcdr_server, file_name):
		self.mcdr_server = mcdr_server
		self.data = None
		self.file_name = file_name

	def read_config(self) -> bool:
		"""
		:return: if there are any missing config entries
		"""
		if os.path.isfile(self.file_name):
			with open(self.file_name, encoding='utf8') as file:
				self.data = yaml.round_trip_load(file)
		return self.check_config()

	def save(self):
		with open(self.file_name, 'w', encoding='utf8') as file:
			yaml.round_trip_dump(self.data, file)

	def touch(self, data, key, default, key_path=''):
		if key not in data:
			data[key] = default
			self.mcdr_server.logger.warning('Option "{}{}" missing, use default value "{}"'.format(key_path, key, default))
			return True
		ret = False
		if isinstance(default, dict):
			divider = ' -> ' if len(key_path) > 0 else ''
			for k, v in default.items():
				ret |= self.touch(data[key], k, v, key_path + divider + key)
		return ret

	def check_config(self) -> bool:
		"""
		:return: if there are any missing config entries
		"""
		flag = False
		if self.data is None:
			self.data = {}
			flag = True
		flag |= self.touch(self.data, 'language', 'en_us')
		flag |= self.touch(self.data, 'working_directory', 'server')
		flag |= self.touch(self.data, 'plugin_folders', ['./plugins'])
		flag |= self.touch(self.data, 'start_command', '')
		flag |= self.touch(self.data, 'parser', 'vanilla_parser')
		flag |= self.touch(self.data, 'encoding', None)
		flag |= self.touch(self.data, 'decoding', None)
		flag |= self.touch(self.data, 'enable_rcon', False)
		flag |= self.touch(self.data, 'rcon_address', '127.0.0.1')
		flag |= self.touch(self.data, 'rcon_port', 25575)
		flag |= self.touch(self.data, 'rcon_password', 'password')
		flag |= self.touch(self.data, 'disable_console_thread', False)
		flag |= self.touch(self.data, 'download_update', True)
		flag |= self.touch(self.data, 'debug', {
			DebugOption.ALL: False,
			DebugOption.PARSER: False,
			DebugOption.PLUGIN: False,
			DebugOption.PERMISSION: False,
		})
		if flag:
			self.save()
		return flag

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
