"""
Single plugin class
"""
import hashlib
import os
import sys
from abc import ABC
from threading import RLock
from typing import Tuple, Any, TYPE_CHECKING

from mcdreforged import constant
from mcdreforged.command.builder.command_node import Literal
from mcdreforged.exception import IllegalCall, IllegalStateError
from mcdreforged.logger import DebugOption
from mcdreforged.plugin.metadata import MetaData
from mcdreforged.plugin.plugin_event import MCDREvent, PluginEvents, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import PluginRegistry, DEFAULT_LISTENER_PRIORITY, HelpMessage
from mcdreforged.rtext import RText
from mcdreforged.utils import misc_util, string_util

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager

GLOBAL_LOAD_LOCK = RLock()


class PluginState:
	UNINITIALIZED = 0  # just created the instance
	LOADED = 1         # loaded the .py file
	READY = 2          # called "on load" event, ready to do anything
	UNLOADING = 3      # just removed from the plugin list, ready to call "on unload" event
	UNLOADED = 4       # unloaded, should never access it


class AbstractPlugin:
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		self.plugin_manager = plugin_manager
		self.mcdr_server = plugin_manager.mcdr_server
		self.file_path = file_path
		self.state = PluginState.UNINITIALIZED
		self.plugin_registry = PluginRegistry(self)

	def is_permanent(self) -> bool:
		raise NotImplementedError()

	def get_metadata(self) -> MetaData:
		raise NotImplementedError()

	def get_fallback_metadata_id(self) -> str:
		raise NotImplementedError()

	def get_name(self) -> str:
		try:
			return self.get_identifier()
		except IllegalCall:
			return repr(self)

	def get_identifier(self) -> str:
		meta_data = self.get_metadata()
		return '{}@{}'.format(meta_data.id, meta_data.version)

	def __str__(self):
		return self.get_name()

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

	# --------------
	#   Life Cycle
	# --------------

	def load(self):
		raise NotImplementedError()

	def ready(self):
		raise NotImplementedError()

	def reload(self):
		raise NotImplementedError()

	def unload(self):
		raise NotImplementedError()

	def remove(self):
		raise NotImplementedError()

	# ----------------
	#   Plugin Event
	# ----------------

	def __assert_allow_to_register(self, target):
		self.assert_state([PluginState.LOADED, PluginState.READY], 'Only plugin in loaded or ready state is allowed to register {}'.format(target))

	def add_event_listener(self, event: PluginEvent, listener: EventListener):
		self.__assert_allow_to_register('listener')
		self.plugin_registry.register_listener(event.id, listener)
		self.mcdr_server.logger.debug('{} is registered for {}'.format(listener, event), option=DebugOption.PLUGIN)

	def add_command(self, node: Literal):
		self.__assert_allow_to_register('command')
		self.plugin_registry.register_command(node)
		self.mcdr_server.logger.debug('{} registered command with root node {}'.format(self, node), option=DebugOption.PLUGIN)

	def add_help_message(self, help_message: HelpMessage):
		self.__assert_allow_to_register('help message')
		self.plugin_registry.register_help_message(help_message)
		if isinstance(help_message, str):
			help_message = RText(help_message)
		self.mcdr_server.logger.debug('Plugin Added help message "{}"'.format(help_message), option=DebugOption.PLUGIN)

	def receive_event(self, event: MCDREvent, args: Tuple[Any, ...]):
		"""
		Directly dispatch an event towards this plugin
		Not suggested to invoke directly in general case since it doesn't have priority control
		"""
		self.assert_state({PluginState.READY, PluginState.UNLOADING}, 'Only plugin in READY or UNLOADING state is allowed to receive events')
		self.mcdr_server.logger.debug('{} directly received {}'.format(self, event), option=DebugOption.PLUGIN)
		for listener in self.plugin_registry.event_listeners.get(event.id, []):
			self.plugin_manager.trigger_listener(listener, args)


class BuiltinPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__(plugin_manager, '**builtin**')


class RegularPlugin(AbstractPlugin):
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		super().__init__(plugin_manager, file_path)
		self.file_name = os.path.basename(file_path)
		self.file_hash = None
		self.instance = None
		self.old_instance = None
		self.newly_loaded_module = []
		# noinspection PyTypeChecker
		self.metadata = None  # type: MetaData

	def is_permanent(self):
		return False

	def get_metadata(self) -> MetaData:
		if self.metadata is None:
			raise IllegalCall('Meta data of plugin {} is not loaded. Plugin state = {}'.format(repr(self), self.state))
		return self.metadata

	def get_fallback_metadata_id(self) -> str:
		return string_util.remove_suffix(self.file_name, constant.PLUGIN_FILE_SUFFIX)

	def __repr__(self):
		return 'RegularPlugin[file={},path={},state={}]'.format(self.file_name, self.file_path, self.state)

	def __register_default_listeners(self):
		for event in PluginEvents.get_event_list():
			if isinstance(event.default_method_name, str):
				func = getattr(self.instance, event.default_method_name, None)
				if callable(func):
					self.add_event_listener(event, EventListener(self, func, DEFAULT_LISTENER_PRIORITY))

	# --------------
	#   Life Cycle
	# --------------

	def __load_instance(self):
		self.file_hash = self.get_file_hash()
		with GLOBAL_LOAD_LOCK:
			previous_modules = sys.modules.copy()
			self.old_instance = self.instance
			try:
				self.instance = misc_util.load_source(self.file_path)
			finally:
				self.newly_loaded_module = [module for module in sys.modules if module not in previous_modules]
		self.metadata = MetaData(self, getattr(self.instance, 'PLUGIN_METADATA', None))
		self.plugin_registry.clear()

	def load(self):
		self.assert_state({PluginState.UNINITIALIZED})
		self.__load_instance()
		self.mcdr_server.logger.debug('Plugin {} loaded from {}, file sha256 = {}'.format(self, self.file_path, self.file_hash))
		self.set_state(PluginState.LOADED)

	def ready(self):
		"""
		Get ready, and register default things (listeners etc.)
		"""
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__register_default_listeners()
		self.set_state(PluginState.READY)

	def reload(self):
		self.assert_state({PluginState.LOADED, PluginState.READY})
		self.__load_instance()
		self.mcdr_server.logger.debug('RegularPlugin {} reloaded, file sha256 = {}'.format(self, self.file_hash))

	def unload(self):
		self.assert_state({PluginState.UNINITIALIZED, PluginState.LOADED, PluginState.READY})
		with GLOBAL_LOAD_LOCK:
			for module in self.newly_loaded_module:
				try:
					sys.modules.pop(module)
				except KeyError:
					self.mcdr_server.logger.critical('Module {} not found when unloading plugin {}'.format(module, repr(self)))
				else:
					self.mcdr_server.logger.debug('Removed module {} when unloading plugin {}'.format(module, repr(self)))
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
