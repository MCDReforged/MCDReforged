# -*- coding: utf-8 -*-
import importlib
import utils.tool as tool


class Plugin:
	def __init__(self, server, file_name):
		self.server = server
		self.file_name = file_name
		self.module = None

	def call(self, func, args=()):
		if hasattr(self.module, func):
			self.module.__dict__[func](*args)

	def load(self):
		self.module = tool.load_source(self.file_name)
		self.call('on_load', (self.server.server_interface, None))

	def unload(self):
		self.call('on_unload', (self.server.server_interface, ))

	def reload(self):
		self.unload()
		old_module = self.module
		self.module = tool.load_source(self.file_name)
		self.call('on_load', (self.server.server_interface, old_module))
