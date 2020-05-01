# -*- coding: utf-8 -*-
import collections
import os
import threading
import hashlib
from utils import tool


HelpMessage = collections.namedtuple('HelpMessage', 'prefix message')


class Plugin:
	def __init__(self, server, file_path):
		self.server = server
		self.file_path = file_path
		self.file_name = os.path.basename(file_path)
		self.plugin_name = tool.remove_suffix(self.file_name, '.py')
		self.module = None
		self.old_module = None
		self.help_messages = []
		self.file_hash = None

	def call(self, func_name, args=()):
		if hasattr(self.module, func_name):
			target = self.module.__dict__[func_name]
			if callable(target):
				thread = PluginThread(target, args, self, func_name)
				thread.start()
				return thread
		return None

	def call_on_load(self):
		self.call('on_load', (self.server.server_interface, self.old_module))

	def call_on_unload(self):
		self.call('on_unload', (self.server.server_interface, ))

	def load(self):
		self.old_module = self.module
		self.module = tool.load_source(self.file_path)
		self.help_messages = []
		with open(self.file_path, 'rb') as file:
			self.file_hash = hashlib.sha512(file.read()).digest()
		self.server.logger.debug('Plugin {} loaded, file sha512 {}'.format(self.file_path, self.file_hash))

	def add_help_message(self, prefix, message):
		self.help_messages.append(HelpMessage(prefix, message))
		self.server.logger.debug('Plugin Added help message "{}: {}"'.format(prefix, message))

	def file_changed(self):
		with open(self.file_path, 'rb') as file:
			file_hash = hashlib.sha512(file.read()).digest()
		return file_hash != self.file_hash


class PluginThread(threading.Thread):
	def __init__(self, target, args, plugin, func_name):
		super().__init__(target=target, args=args, name='{}@{}'.format(func_name, plugin.plugin_name))
		self.daemon = True
		self.plugin = plugin
		self.func_name = func_name

	def run(self):
		try:
			super().run()
		except:
			self.plugin.server.logger.exception('Error calling {} in plugin {}'.format(self.func_name, self.plugin.plugin_name))
