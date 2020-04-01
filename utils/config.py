# -*- coding: utf-8 -*-

import ruamel.yaml as yaml


class Config:
	def __init__(self, file_name):
		self.data = None
		self.file_name = file_name
		self.read_config()

	def read_config(self):
		with open(self.file_name, encoding='utf8') as file:
			self.data = yaml.round_trip_load(file)

	def __getitem__(self, item):
		return self.data[item]
