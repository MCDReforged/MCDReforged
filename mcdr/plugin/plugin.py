"""
Single plugin class
"""
import hashlib
import os
import sys
from threading import RLock
from typing import Tuple, Any

from mcdr.exception import IllegalCall, IllegalStateError
from mcdr.logger import DebugOption
from mcdr.plugin.metadata import MetaData
from mcdr.plugin.plugin_event import PluginEvent, PluginEvents
from mcdr.plugin.plugin_registry import PluginRegistry
from mcdr.plugin.plugin_thread import PluginThreadPool, TaskData
from mcdr.rtext import RText, RTextBase
from mcdr.utils import misc_util

GLOBAL_LOAD_LOCK = RLock()


class PluginState:
	UNINITIALIZED = 0  # just created the instance
	LOADED = 1         # loaded the .py file
	READY = 2          # called "on load" event, ready to do anything
	UNLOADING = 3      # just removed from the plugin list, ready to call "on unload" event
	UNLOADED = 4       # unloaded, should never access it


class Plugin:
	def __init__(self, plugin_manager, file_path):
		self.plugin_manager = plugin_manager
		self.server = plugin_manager.server
		self.file_path = file_path
		self.file_name = os.path.basename(file_path)
		self.file_hash = None
		self.instance = None
		self.old_instance = None
		self.newly_loaded_module = []
		self.thread_pool = self.plugin_manager.thread_pool  # type: PluginThreadPool
		# noinspection PyTypeChecker
		self.meta_data = None  # type: MetaData
		self.state = PluginState.UNINITIALIZED
		self.registry = PluginRegistry(self)

	def get_meta_data(self) -> MetaData:
		if self.meta_data is None:
			raise IllegalCall('Meta data of plugin {} is not loaded. Plugin state = {}'.format(repr(self), self.state))
		return self.meta_data

	def get_name(self) -> str:
		try:
			return str(self)
		except IllegalCall:
			return repr(self)

	# ----------------
	#   Plugin State
	# ----------------

	def set_state(self, state):
		self.state = state

	def in_states(self, states):
		return self.state in states

	def assert_state(self, states, extra_message=None):
		if not self.in_states(states):
			msg = '{} state assertion failed, excepts {} but founded {}.'.format(repr(self), states, self.state)
			if extra_message is not None:
				msg += ' ' + extra_message
			raise IllegalStateError(msg)

	# -----------------
	#   Load / Unload
	# -----------------

	def __load_instance(self):
		self.file_hash = self.get_file_hash()
		with GLOBAL_LOAD_LOCK:
			previous_modules = sys.modules.copy()
			self.old_instance = self.instance
			try:
				self.instance = misc_util.load_source(self.file_path)
			finally:
				self.newly_loaded_module = [module for module in sys.modules if module not in previous_modules]
		self.meta_data = MetaData(self, self.instance.__dict__.get('PLUGIN_METADATA'))
		self.registry.clear()

	def load(self):
		self.assert_state({PluginState.UNINITIALIZED})
		self.__load_instance()
		self.server.logger.debug('Plugin {} loaded from {}, file sha256 = {}'.format(self, self.file_path, self.file_hash))
		self.set_state(PluginState.LOADED)

	def ready(self):
		self.assert_state({PluginState.LOADED})
		self.__register_default_listeners()
		self.set_state(PluginState.READY)

	def reload(self):
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__load_instance()
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
		self.set_state(PluginState.UNLOADING)

	def remove(self):
		self.assert_state({PluginState.UNLOADING})
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
		return '{}@{}'.format(meta_data.id, meta_data.version)

	def __repr__(self):
		return 'Plugin[file={},path={},state={}]'.format(self.file_name, self.file_path, self.state)

	# ----------------
	#   Plugin Event
	# ----------------

	def __register_default_listeners(self):
		for event in PluginEvents.get_event_list():
			if isinstance(event.default_method_name, str):
				func = self.instance.__dict__.get(event.default_method_name)
				if callable(func):
					self.add_listener(event, func)

	def add_listener(self, event: PluginEvent or str, callback):
		self.assert_state([PluginState.LOADED, PluginState.READY], 'Only plugin in loaded or ready state is allowed to register listeners')
		self.registry.register_listener(event, callback)
		self.server.logger.debug('{} registered event listener {} for event {}'.format(self, callback, event), option=DebugOption.PLUGIN)

	def add_help_message(self, prefix: str, help_message: str or RTextBase):
		self.registry.register_help_message(prefix, help_message)
		if isinstance(help_message, str):
			help_message = RText(help_message)
		self.server.logger.debug('Plugin Added help message "{}: {}"'.format(prefix, help_message), option=DebugOption.PLUGIN)

	def receive_event(self, event: PluginEvent, args: Tuple[Any, ...]):
		self.assert_state({PluginState.READY, PluginState.UNLOADING}, 'Only plugin in READY or UNLOADING state is allowed to receive events')
		for listener in self.registry.event_listeners.get(event, []):
			self.thread_pool.add_task(TaskData(callback=lambda: listener(*args), plugin=self), False)
