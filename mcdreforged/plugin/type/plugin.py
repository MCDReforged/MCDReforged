"""
Single plugin class
"""
from enum import Enum, auto
from typing import Tuple, Any, TYPE_CHECKING

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.plugin_event import MCDREvent, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import PluginRegistry, HelpMessage
from mcdreforged.utils.exception import IllegalCallError, IllegalStateError
from mcdreforged.utils.logger import DebugOption
from mcdreforged.utils.types import TranslationKeyDictNested

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


class PluginState(Enum):
	UNINITIALIZED = auto()  # just created the instance
	LOADING = auto()        # loading the .py entrance file
	LOADED = auto()         # loaded the .py entrance file
	READY = auto()          # called "on load" event, ready to do anything
	UNLOADING = auto()      # just removed from the plugin list, ready to call "on unload" event
	UNLOADED = auto()       # unloaded, should never access it


class AbstractPlugin:
	def __init__(self, plugin_manager: 'PluginManager', file_path: str):
		self.plugin_manager = plugin_manager
		self.mcdr_server = plugin_manager.mcdr_server
		self.plugin_path = file_path
		self.state = PluginState.UNINITIALIZED
		self.plugin_registry = PluginRegistry(self, plugin_manager.registry_storage)

		from mcdreforged.plugin.server_interface import PluginServerInterface
		self.server_interface = PluginServerInterface(self.mcdr_server, self)

	def is_permanent(self) -> bool:
		return False

	def is_regular(self) -> bool:
		return False

	def get_metadata(self) -> Metadata:
		raise NotImplementedError()

	def get_id(self) -> str:
		return self.get_metadata().id

	def get_meta_name(self) -> str:
		return self.get_metadata().name

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

	def __repr__(self):
		raise NotImplementedError()

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

	# -------------------
	#   Plugin Registry
	# -------------------

	def __assert_allow_to_register(self, target):
		self.assert_state([PluginState.LOADED, PluginState.READY], 'Only plugin in loaded or ready state is allowed to register {}'.format(target))

	def register_event_listener(self, event: PluginEvent, listener: EventListener):
		self.__assert_allow_to_register('listener')
		self.plugin_registry.register_event_listener(event.id, listener)
		self.mcdr_server.logger.debug('{} is registered for {}'.format(listener, event), option=DebugOption.PLUGIN)

	def register_command(self, node: Literal):
		self.__assert_allow_to_register('command')
		self.plugin_registry.register_command(node)
		self.mcdr_server.logger.debug('{} registered command with root node {}'.format(self, node), option=DebugOption.PLUGIN)

	def register_help_message(self, help_message: HelpMessage):
		self.__assert_allow_to_register('help message')
		self.plugin_registry.register_help_message(help_message)
		self.mcdr_server.logger.debug('{} registered help message "{}"'.format(self, help_message), option=DebugOption.PLUGIN)

	def receive_event(self, event: MCDREvent, args: Tuple[Any, ...]):
		"""
		Directly dispatch an event towards this plugin
		Not suggested to invoke directly in general case since it doesn't have priority control
		"""
		self.assert_state({PluginState.READY, PluginState.UNLOADING}, 'Only plugin in READY or UNLOADING state is allowed to receive events')
		self.mcdr_server.logger.debug('{} directly received {}'.format(self, event), option=DebugOption.PLUGIN)
		for listener in self.plugin_registry.event_listeners.get(event.id, []):
			self.plugin_manager.trigger_listener(listener, args)

	def register_translation(self, language: str, mapping: TranslationKeyDictNested):
		self.__assert_allow_to_register('translation')
		self.plugin_registry.register_translation(language, mapping)
		self.mcdr_server.logger.debug('{} registered translation for {} with at least {} entries'.format(self, language, len(mapping)), option=DebugOption.PLUGIN)
