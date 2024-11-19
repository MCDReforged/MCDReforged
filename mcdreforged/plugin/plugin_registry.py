import collections
import dataclasses
from typing import Dict, List, Callable, Any, TYPE_CHECKING, Union, Optional

from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.handler.plugin_provided_server_handler_holder import PluginProvidedServerHandlerHolder
from mcdreforged.info_reactor.info_filter import InfoFilter, InfoFilterHolder
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.plugin.plugin_event import EventListener
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_utils, class_utils
from mcdreforged.utils.types.message import TranslationStorage, TranslationKeyDictRich, MessageText, \
	TranslationKeyDictNested

if TYPE_CHECKING:
	from mcdreforged.handler.server_handler import ServerHandler
	from mcdreforged.plugin.type.plugin import AbstractPlugin
	from mcdreforged.plugin.plugin_manager import PluginManager

DEFAULT_LISTENER_PRIORITY = 1000


class HelpMessage:
	def __init__(self, plugin: 'AbstractPlugin', prefix: str, message: Union[MessageText, TranslationKeyDictRich], permission: int):
		self.plugin = plugin
		self.prefix = prefix

		self.message: RTextBase
		if isinstance(message, RTextMCDRTranslation):
			self.message = message
		elif isinstance(message, dict):
			self.message = RTextMCDRTranslation.from_translation_dict(message)
		else:
			self.message = RTextBase.from_any(message)

		self.permission = permission
		self.__prefix_lower = self.prefix.lower()

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		if self.__prefix_lower != other.__prefix_lower:
			return self.__prefix_lower < other.__prefix_lower
		return self.prefix < other.prefix

	def __repr__(self):
		return class_utils.represent(self, {
			'prefix': self.prefix,
			'message': self.message,
			'permission': self.permission,
		})


@dataclasses.dataclass(frozen=True)
class PluginCommandHolder:
	"""
	A tuple for tracking the plugin of the node
	"""
	plugin: 'AbstractPlugin'
	node: Literal
	allow_duplicates: bool


class _BasePluginRegistry:
	def __init__(self):
		self._event_listeners: Dict[str, List[EventListener]] = collections.defaultdict(list)
		self._help_messages: List[HelpMessage] = []
		self._command_roots: List[PluginCommandHolder] = []
		self._translations: TranslationStorage = collections.defaultdict(dict)
		self._server_handler: Optional['ServerHandler'] = None
		self._info_filters: List[InfoFilterHolder] = []

	def clear(self):
		self._event_listeners.clear()
		self._help_messages.clear()
		self._command_roots.clear()
		self._translations.clear()
		self._server_handler = None
		self._info_filters.clear()

	def get_event_listeners(self, event_id: str) -> List[EventListener]:
		return self._event_listeners.get(event_id, [])

	@property
	def help_messages(self) -> List[HelpMessage]:
		return self._help_messages

	@property
	def translations(self) -> TranslationStorage:
		return self._translations


class PluginRegistry(_BasePluginRegistry):
	def __init__(self, plugin: 'AbstractPlugin', target_storage: 'PluginRegistryStorage'):
		super().__init__()
		self.plugin = plugin
		self.target_storage = target_storage

	def register_help_message(self, help_message: HelpMessage):
		self._help_messages.append(help_message)

	def register_event_listener(self, event_id: str, listener: EventListener):
		self._event_listeners[event_id].append(listener)

	def register_command(self, node: Literal, allow_duplicates: bool):
		if not isinstance(node, Literal):
			raise TypeError('Only Literal node is accepted to be a root node')
		self._command_roots.append(PluginCommandHolder(self.plugin, node, allow_duplicates))

	def register_translation(self, language: str, mapping: TranslationKeyDictNested):
		# Translation should be updated immediately
		translation_utils.update_storage(self._translations, language, mapping)
		translation_utils.update_storage(self.target_storage._translations, language, mapping)

	def register_server_handler(self, server_handler: 'ServerHandler'):
		self._server_handler = server_handler

	def register_info_filter(self, info_filter: InfoFilter):
		self._info_filters.append(InfoFilterHolder(info_filter, self.plugin))


class PluginRegistryStorage(_BasePluginRegistry):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__()
		self.plugin_manager = plugin_manager
		self.logger = plugin_manager.logger

		self.__server_handler_plugin: Optional['AbstractPlugin'] = None

	@override
	def clear(self):
		super().clear()
		self.__server_handler_plugin = None

	def collect(self, plugin: 'AbstractPlugin', plugin_registry: _BasePluginRegistry):
		for event_id, plg_listeners in plugin_registry._event_listeners.items():
			self._event_listeners[event_id].extend(plg_listeners)
		self._help_messages.extend(plugin_registry._help_messages)
		self._command_roots.extend(plugin_registry._command_roots)
		translation_utils.extend_storage(self._translations, plugin_registry._translations)

		if plugin_registry._server_handler is not None:
			if self._server_handler is not None:
				self.logger.warning('Found multiple plugin-defined server handlers: previous {} by plugin {}, current {} by plugin {}. Ignoring the current one'.format(
					repr(self._server_handler.get_name()), self.__server_handler_plugin, repr(plugin_registry._server_handler.get_name()), plugin
				))
			else:
				self.__server_handler_plugin = plugin
				self._server_handler = plugin_registry._server_handler

		self._info_filters.extend(plugin_registry._info_filters)

	def arrange(self):
		self._help_messages.sort()
		for listeners in self._event_listeners.values():
			listeners.sort()

	def export_commands(self, exporter: Callable[[PluginCommandHolder], Any]):
		for pch in self._command_roots:
			exporter(pch)

	def export_server_handler(self, exporter: Callable[[Optional[PluginProvidedServerHandlerHolder]], Any]):
		if self._server_handler is not None:
			exporter(PluginProvidedServerHandlerHolder(self._server_handler, self.__server_handler_plugin))
		else:
			exporter(None)

	def export_info_filters(self, exporter: Callable[[InfoFilterHolder], Any]):
		for info_filter in self._info_filters:
			exporter(info_filter)
