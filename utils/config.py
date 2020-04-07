# -*- coding: utf-8 -*-

import os
import ruamel.yaml as yaml


class Config:
	def __init__(self, server, file_name):
		self.server = server
		self.data = None
		self.file_name = file_name
		self.read_config()

	def read_config(self):
		if os.path.isfile(self.file_name):
			with open(self.file_name, encoding='utf8') as file:
				self.data = yaml.round_trip_load(file)
		self.check_config()

	def save(self):
		with open(self.file_name, 'w') as file:
			yaml.round_trip_dump(self.data, file)

	def touch(self, key, default):
		if self.data is None:
			self.data = {}
		if key not in self.data:
			self.data[key] = default
			self.server.logger.warning('Option "{}" missing, use default value "{}"'.format(key, default))
			return True
		return False

	def check_config(self):
		flag = False
		flag |= self.touch('language', 'en_us')
		flag |= self.touch('working_directory', 'server')
		flag |= self.touch('start_command', '')
		flag |= self.touch('parser', 'vanilla_parser')
		flag |= self.touch('encoding', None)
		flag |= self.touch('decoding', None)
		flag |= self.touch('console_command_prefix', '!!')
		flag |= self.touch('enable_rcon', False)
		flag |= self.touch('rcon_address', '127.0.0.1')
		flag |= self.touch('rcon_port', 25575)
		flag |= self.touch('rcon_password', 'password')
		flag |= self.touch('disable_console_thread', False)
		flag |= self.touch('debug_mode', False)
		if flag:
			self.server.logger.warning('Some options in the config file is missing, use default value')
			self.server.logger.warning('Remember to update the config file as soon as possible')
			self.save()

	def __getitem__(self, item):
		return self.data[item]
