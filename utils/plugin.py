# -*- coding: utf-8 -*-
import os
import threading
import traceback

import utils.tool as tool


class Plugin:
	def __init__(self, server, file_name):
		self.server = server
		self.file_name = file_name
		self.plugin_name = os.path.basename(self.file_name).rstrip('.py')
		self.module = None

	def call(self, func, args=(), new_thread=True):
		if hasattr(self.module, func):
			target = self.module.__dict__[func]
			if callable(target):
				func_name = '{}@{}'.format(func, self.plugin_name)
				return tool.start_thread(target, args, func_name)
		return None

	def load(self, old_module=None):
		self.module = tool.load_source(self.file_name)
		self.call('on_load', (self.server.server_interface, old_module))

	def unload(self):
		self.call('on_unload', (self.server.server_interface, ))

	def reload(self):
		self.unload()
		old_module = self.module
		self.load(old_module)
