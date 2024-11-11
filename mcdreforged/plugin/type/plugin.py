"""
Single plugin class
"""
from abc import abstractmethod
from typing import Tuple, Any, TYPE_CHECKING, Collection, Optional

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.info_reactor.info_filter import InfoFilter
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.meta.version import Version
from mcdreforged.plugin.plugin_event import MCDREvent, EventListener, PluginEvent
from mcdreforged.plugin.plugin_registry import PluginRegistry, HelpMessage
from mcdreforged.plugin.type.common import PluginState, PluginType
from mcdreforged.utils import class_utils
from mcdreforged.utils.exception import IllegalCallError, IllegalStateError
from mcdreforged.utils.types.message import TranslationKeyDictNested

if TYPE_CHECKING:
	from mcdreforged.handler.server_handler import ServerHandler
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.builtin_plugin import BuiltinPlugin
	from mcdreforged.plugin.type.regular_plugin import RegularPlugin


class AbstractPlugin:
	def __init__(self, plugin_manager: 'PluginManager'):
		self.plugin_manager = plugin_manager
		self.mcdr_server = plugin_manager.mcdr_server
		self.state = PluginState.UNINITIALIZED
		self.plugin_registry = PluginRegistry(self, plugin_manager.registry_storage)

		from mcdreforged.plugin.si.plugin_server_interface import PluginServerInterface
		self.server_interface = PluginServerInterface(self.mcdr_server, self)

	def is_builtin(self) -> bool:
		from mcdreforged.plugin.type.builtin_plugin import BuiltinPlugin
		return isinstance(self, BuiltinPlugin)

	def is_regular(self) -> bool:
		from mcdreforged.plugin.type.regular_plugin import RegularPlugin
		return isinstance(self, RegularPlugin)

	@abstractmethod
	def get_type(self) -> PluginType:
		raise NotImplementedError()

	@abstractmethod
	def get_metadata(self) -> Metadata:
		raise NotImplementedError()

	def get_id(self) -> str:
		return self.get_metadata().id

	def get_version(self) -> Version:
		return self.get_metadata().version

	def get_meta_name(self) -> str:
		return self.get_metadata().name

	@abstractmethod
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

	def _create_repr_fields(self) -> dict:
		return {
			'state': self.state,
		}

	def __repr__(self):
		return class_utils.represent(self, fields=self._create_repr_fields())

	def __str__(self):
		return self.get_name()

	# ----------------
	#   Plugin State
	# ----------------

	def set_state(self, state: PluginState):
		self.state = state

	def in_states(self, states: Collection[PluginState]):
		return self.state in states

	def assert_state(self, states: Collection[PluginState], extra_message: Optional[str] = None):
		if not self.in_states(states):
			msg = '{} state assertion failed, excepts {} but founded {}.'.format(repr(self), states, self.state)
			if extra_message is not None:
				msg += ' ' + extra_message
			raise IllegalStateError(msg)

	# --------------
	#   Life Cycle
	# --------------

	#  load -> ready -> unload -> remove
	#            ^        /
	#             \      v
	#              reload

	@abstractmethod
	def load(self):
		"""
		The first operation to the plugin, read some basic information
		"""
		raise NotImplementedError()

	@abstractmethod
	def ready(self):
		"""
		The plugin is ready to be fully loaded. It's ready to handle its entrypoint module
		"""
		raise NotImplementedError()

	@abstractmethod
	def reload(self):
		"""
		Reload the plugin
		Notes: invoke :meth:`unload` before invoking this method
		"""
		raise NotImplementedError()

	@abstractmethod
	def unload(self):
		"""
		Unload the plugin. Due to plugin unload / reload
		"""
		raise NotImplementedError()

	@abstractmethod
	def remove(self):
		"""
		The last operation to the plugin
		Notes: invoke :meth:`unload` before invoking this method
		"""
		raise NotImplementedError()

	# -------------------
	#   Plugin Registry
	# -------------------

	def __assert_allow_to_register(self, target):
		self.assert_state([PluginState.LOADED, PluginState.READY], 'Only plugin in loaded or ready state is allowed to register {}'.format(target))

	def register_event_listener(self, event: PluginEvent, listener: EventListener):
		self.__assert_allow_to_register('listener')
		self.plugin_registry.register_event_listener(event.id, listener)
		self.mcdr_server.logger.mdebug('{} is registered for {}'.format(listener, event), option=DebugOption.PLUGIN)

	def register_command(self, node: Literal, *, allow_duplicates: bool = False):
		self.__assert_allow_to_register('command')
		self.plugin_registry.register_command(node, allow_duplicates)
		self.mcdr_server.logger.mdebug('{} registered command with root node {}'.format(self, node), option=DebugOption.PLUGIN)

	def register_help_message(self, help_message: HelpMessage):
		self.__assert_allow_to_register('help message')
		self.plugin_registry.register_help_message(help_message)
		self.mcdr_server.logger.mdebug('{} registered help message {}'.format(self, help_message), option=DebugOption.PLUGIN)

	def register_translation(self, language: str, mapping: TranslationKeyDictNested):
		self.__assert_allow_to_register('translation')
		self.plugin_registry.register_translation(language, mapping)
		self.mcdr_server.logger.mdebug('{} registered translation for {} with at least {} entries'.format(self, language, len(mapping)), option=DebugOption.PLUGIN)

	def register_server_handler(self, server_handler: 'ServerHandler'):
		self.__assert_allow_to_register('server_handler')
		self.plugin_registry.register_server_handler(server_handler)

	def register_info_filter(self, info_filter: InfoFilter):
		self.__assert_allow_to_register('info_filter')
		self.plugin_registry.register_info_filter(info_filter)

	# -------------------
	#    Plugin Events
	# -------------------

	def receive_event(self, event: MCDREvent, args: Tuple[Any, ...]):
		"""
		Directly dispatch an event towards this plugin
		Not suggested to invoke directly in general case since it doesn't have priority control
		"""
		self.assert_state({PluginState.READY}, 'Only plugin in READY state is allowed to receive events')
		self.mcdr_server.logger.mdebug('{} directly received {}'.format(self, event), option=DebugOption.PLUGIN)
		for listener in self.plugin_registry.get_event_listeners(event.id):
			try:
				self.plugin_manager.trigger_listener(listener, args).result()
			except Exception:
				self.mcdr_server.logger.exception('Direct listener triggering failed, plugin {}, event {}, listener {}'.format(self, event, listener))
