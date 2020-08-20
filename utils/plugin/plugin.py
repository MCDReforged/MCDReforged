# -*- coding: utf-8 -*-
import collections
import hashlib
import os
import sys
from inspect import getfullargspec

from utils import tool
from utils.plugin.plugin_thread import TaskData

HelpMessage = collections.namedtuple('HelpMessage', 'prefix message plugin_name')


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
		self.loaded_modules = []
		self.thread_pool = self.server.plugin_manager.thread_pool
		self.load_lock = self.server.plugin_manager.plugin_load_lock

	def call(self, func_name, args, forced_new_thread=False):
		"""
		Try to call a function named func_name in this plugin
		If this plugin has not implement a callable object named func_name nothing will happen
		If the argument count of the function is not matched an error message will be logged
		Otherwise a function call task will be created in the thread pool of MCDR

		:param str func_name: The name of the function to call
		:param args: A tuple of args using during calling the function. It can also be a list of potential args and in
		that case it will try to find an args in the list which has the same length of the accepted argument length of
		the function the plugin implements
		:type args: tuple or list[tuple]
		:param forced_new_thread: If set to True, create a independent thread for the call
		:return: A threading.Thread instance if forced_new_thread is True else None
		:rtype: threading.Thread or None
		"""

		def argument_match(argument):
			return required_args_length_min <= len(argument) and (len(argument) <= required_args_length_max or spec.varargs)

		if hasattr(self.module, func_name):
			func = self.module.__dict__[func_name]
			if callable(func):
				spec = getfullargspec(func)
				required_args_length_max = len(spec.args)
				required_args_length_min = required_args_length_max - len(spec.defaults) if spec.defaults else required_args_length_max
				required_args_msg = (
					'>={}'.format(required_args_length_min) if spec.varargs
					else str(required_args_length_max) if required_args_length_max == required_args_length_min
					else '{}-{}'.format(required_args_length_min, required_args_length_max)
				)
				correct_args = None
				if type(args) is tuple:
					excepted_args = str(len(args))
					if argument_match(args):
						correct_args = args
				elif type(args) is list:
					excepted_args = '[{}]'.format(', '.join([str(len(x)) for x in args]))
					for args_candidate in args:
						if argument_match(args_candidate):
							correct_args = args_candidate
							break
				else:
					raise TypeError('args should be a tuple or a list')

				if correct_args is None:
					self.server.logger.error(self.server.t('plugin.call.args_not_matched', func_name, self.plugin_name, required_args_msg, excepted_args))
				else:
					return self.thread_pool.add_task(TaskData(func, correct_args, func_name, self), forced_new_thread=forced_new_thread)

	def load(self):
		with self.load_lock:
			self.old_module = self.module
			previous_modules = sys.modules.copy()
			self.module = tool.load_source(self.file_path)
			self.loaded_modules = [module for module in sys.modules.copy() if module not in previous_modules]
			self.help_messages = []
			self.file_hash = self.get_file_hash()
			self.server.logger.debug('Plugin {} loaded, file sha256 = {}'.format(self.file_path, self.file_hash))

	# on_load event sometimes cannot be called right after plugin gets loaded, so here's its separated method for the call
	def call_on_load(self):
		self.call('on_load', (self.server.server_interface, self.old_module))

	def unload(self):
		self.call('on_unload', (self.server.server_interface, ))
		self.unload_modules()

	def unload_modules(self):
		with self.load_lock:
			for module in self.loaded_modules:
				try:
					del sys.modules[module]
				except KeyError:
					self.server.logger.critical('Module {} not found when unloading plugin {}'.format(module, self.plugin_name))
				else:
					self.server.logger.debug('Removed module {} when unloading plugin {}'.format(module, self.plugin_name))
			self.loaded_modules = []

	def add_help_message(self, prefix, message):
		self.help_messages.append(HelpMessage(prefix, message, self.file_name))
		self.server.logger.debug('Plugin Added help message "{}: {}"'.format(prefix, message))

	def get_file_hash(self):
		if os.path.isfile(self.file_path):
			with open(self.file_path, 'rb') as file:
				return hashlib.sha256(file.read()).hexdigest()
		else:
			return None

	def file_changed(self):
		return self.get_file_hash() != self.file_hash

