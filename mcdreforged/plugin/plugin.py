"""
Single plugin class
"""
from abc import ABC
from typing import Tuple, Any, TYPE_CHECKING

from mcdreforged.command.builder.command_node import Literal
from mcdreforged.exception import IllegalCallError, IllegalStateError
from mcdreforged.logger import DebugOption
from mcdreforged.plugin.metadata import MetaData
from mcdreforged.plugin.plugin_event import MCDREvent, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import PluginRegistry, HelpMessage

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


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
		return False

	def is_regular(self) -> bool:
		return False

	def get_metadata(self) -> MetaData:
		raise NotImplementedError()

	def get_fallback_metadata_id(self) -> str:
		raise NotImplementedError()

	def get_name(self) -> str:
		try:
			return self.get_identifier()
		except IllegalCallError:
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


class PermanentPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__(plugin_manager, '**builtin**')

	def is_permanent(self) -> bool:
		return True
