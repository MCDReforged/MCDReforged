# -*- coding: utf-8 -*-

from . import config, constant


class Server:
	def __init__(self):
		self.config = config.Config(constant.CONFIG_FILE)

	def tick(self):
		pass

	def start(self):
		pass

