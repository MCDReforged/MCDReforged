import collections
from typing import Dict, List, Callable, Any, TYPE_CHECKING, Union

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.minecraft.rtext import RTextBase
from mcdreforged.plugin.plugin_event import EventListener
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_util
from mcdreforged.utils.types import TranslationStorage, TranslationKeyDictRich, MessageText, \
	TranslationKeyDictNested

if TYPE_CHECKING:
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
		return 'HelpMessage[prefix={},message={},permission={}]'.format(self.prefix, self.message, self.permission)


class PluginCommandNode:
	"""
	A Tuple like data class for tracking the plugin of the node
	"""
	def __init__(self, plugin: 'AbstractPlugin', node: Literal):
		self.plugin = plugin
		self.node = node


class AbstractPluginRegistry:
	def __init__(self):
		self.event_listeners = collections.defaultdict(list)  # type: Dict[str, List[EventListener]]
		self.help_messages: List[HelpMessage] = []
		self.command_roots: List[PluginCommandNode] = []
		self.translations: TranslationStorage = collections.defaultdict(dict)

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()
		self.command_roots.clear()


class PluginRegistry(AbstractPluginRegistry):
	def __init__(self, plugin: 'AbstractPlugin', target_storage: 'PluginRegistryStorage'):
		super().__init__()
		self.plugin = plugin
		self.target_storage = target_storage

	def register_help_message(self, help_message: HelpMessage):
		self.help_messages.append(help_message)

	def register_event_listener(self, event_id: str, listener: EventListener):
		self.event_listeners[event_id].append(listener)

	def register_command(self, node: Literal):
		if not isinstance(node, Literal):
			raise TypeError('Only Literal node is accepted to be a root node')
		self.command_roots.append(PluginCommandNode(self.plugin, node))

	def register_translation(self, language: str, mapping: TranslationKeyDictNested):
		# Translation should be updated immediately
		translation_util.update_storage(self.translations, language, mapping)
		translation_util.update_storage(self.target_storage.translations, language, mapping)


class PluginRegistryStorage(AbstractPluginRegistry):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__()
		self.plugin_manager = plugin_manager

	def collect(self, registry: AbstractPluginRegistry):
		for event_id, plg_listeners in registry.event_listeners.items():
			self.event_listeners[event_id].extend(plg_listeners)
		self.help_messages.extend(registry.help_messages)
		self.command_roots.extend(registry.command_roots)

	def arrange(self):
		self.help_messages.sort()
		for listeners in self.event_listeners.values():
			listeners.sort()

	def export_commands(self, exporter: Callable[[PluginCommandNode], Any]):
		for node in self.command_roots:
			exporter(node)
