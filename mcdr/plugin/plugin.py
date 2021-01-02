"""
Single plugin class
"""
import collections
import hashlib
import os
import sys
from threading import RLock
from typing import Dict, Callable, List

from mcdr import tool
from mcdr.exception import IllegalCall, IllegalStateError
from mcdr.plugin.metadata import MetaData
from mcdr.plugin.plugin_event import Event

HelpMessage = collections.namedtuple('HelpMessage', 'prefix message plugin_name')
GLOBAL_LOAD_LOCK = RLock()


class PluginState:
	UNINITIALIZED = 0  # just created the instance
	LOADED = 1         # loaded the .py file
	READY = 2          # called on_load event
	UNLOADED = 3       # unloaded


class Plugin:
	def __init__(self, server, file_path):
		self.server = server
		self.file_path = file_path
		self.file_name = os.path.basename(file_path)
		self.file_hash = None
		self.instance = None
		self.old_instance = None
		self.newly_loaded_module = []
		# noinspection PyTypeChecker
		self.meta_data = None  # type: MetaData
		self.state = PluginState.UNINITIALIZED
		self.event_listeners = {}  # type: Dict[Event, List[Callable]]

	def set_state(self, state):
		self.state = state

	def assert_state(self, states, extra_message=None):
		if self.state not in states:
			msg = '{} state assertion failed, excepts {} but founded {}.'.format(repr(self), self.state, states)
			if extra_message is not None:
				msg += ' ' + extra_message
			raise IllegalStateError(msg)

	def get_meta_data(self) -> MetaData:
		if self.meta_data is None:
			raise IllegalCall('Meta data of plugin {} is not loaded. Plugin state = {}'.format(repr(self), self.state))
		return self.meta_data

	# -----------------
	#   Load / Unload
	# -----------------

	def __load(self):
		self.file_hash = self.get_file_hash()
		with GLOBAL_LOAD_LOCK:
			previous_modules = sys.modules.copy()
			self.old_instance = self.instance
			try:
				self.instance = tool.load_source(self.file_path)
			finally:
				self.newly_loaded_module = [module for module in sys.modules if module not in previous_modules]
		self.meta_data = MetaData(self, self.instance.__dict__.get('PLUGIN_METADATA'))

	def load(self):
		self.assert_state({PluginState.UNINITIALIZED})
		self.__load()
		self.server.logger.debug('Plugin {} loaded from {}, file sha256 = {}'.format(self, self.file_path, self.file_hash))
		self.set_state(PluginState.LOADED)

	def reload(self):
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__load()
		self.server.logger.debug('Plugin {} reloaded, file sha256 = {}'.format(self, self.file_hash))

	def unload(self):
		self.assert_state({PluginState.UNINITIALIZED, PluginState.LOADED, PluginState.READY})
		with GLOBAL_LOAD_LOCK:
			for module in self.newly_loaded_module:
				try:
					sys.modules.pop(module)
				except KeyError:
					self.server.logger.critical('Module {} not found when unloading plugin {}'.format(module, repr(self)))
				else:
					self.server.logger.debug('Removed module {} when unloading plugin {}'.format(module, repr(self)))
			self.newly_loaded_module.clear()
		self.set_state(PluginState.UNLOADED)

	# ---------------
	#   Plugin File
	# ---------------

	def file_exists(self):
		return os.path.isfile(self.file_path)

	def file_changed(self):
		return self.get_file_hash() != self.file_hash

	def get_file_hash(self):
		if self.file_exists():
			with open(self.file_path, 'rb') as file:
				return hashlib.sha256(file.read()).hexdigest()
		else:
			return None

	# -----------------
	#   Magic Methods
	# -----------------

	def __str__(self):
		meta_data = self.get_meta_data()
		return '{}@{}'.format(meta_data.id, meta_data.id)

	def __repr__(self):
		return 'Plugin[{},path={},state={}]'.format(self.file_name, self.file_path, self.state)

	# ----------------
	#   Plugin Event
	# ----------------

	def receive_event(self, event: Event):
		self.assert_state({PluginState.READY}, 'Only plugin in ready state is allowed to receive events')
		for listener in self.event_listeners.get(event, ()):
			listener()  # TODO
