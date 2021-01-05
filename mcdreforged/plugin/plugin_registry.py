from typing import Dict, List, Callable, Any

from mcdreforged.command.builder.command_node import Literal
from mcdreforged.permission_manager import PermissionLevel
from mcdreforged.plugin.plugin_event import EventListener
from mcdreforged.rtext import RTextBase

DEFAULT_LISTENER_PRIORITY = 1000


class HelpMessage:
	def __init__(self, plugin, prefix: str, message: RTextBase, permission: int):
		self.plugin = plugin
		self.prefix = prefix
		self.message = message
		self.permission = permission

	def __get_compare_key(self):
		return self.prefix[:1].upper() + self.prefix[1:]

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.__get_compare_key() < other.__get_compare_key()

	def __repr__(self):
		return 'HelpMessage[prefix={},message={},permission={}]'.format(self.prefix, self.message.to_plain_text(), self.permission)


class PluginRegistry:
	def __init__(self, plugin):
		self.plugin = plugin
		self.event_listeners = {}  # type: Dict[str, List[EventListener]]
		self.help_messages = []
		self.command_roots = []  # type: List[Literal]

	def register_help_message(self, help_message: HelpMessage):
		self.help_messages.append(help_message)

	def register_listener(self, event_id: str, listener: EventListener):
		listeners = self.event_listeners.get(event_id, [])
		listeners.append(listener)
		self.event_listeners[event_id] = listeners

	def register_command(self, node: Literal):
		self.command_roots.append(node)

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()
		self.command_roots.clear()


class PluginManagerRegistry:
	def __init__(self, plugin_manager):
		self.plugin_manager = plugin_manager
		self.event_listeners = {}  # type: Dict[str, List[EventListener]]
		self.help_messages = []  # type: List[HelpMessage]
		self.command_roots = []  # type: List[Literal]

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()
		self.command_roots.clear()

	def collect(self, registry: PluginRegistry):
		for event_id, plg_listeners in registry.event_listeners.items():
			listeners = self.event_listeners.get(event_id, [])
			listeners.extend(plg_listeners)
			self.event_listeners[event_id] = listeners
		self.help_messages.extend(registry.help_messages)
		self.command_roots.extend(registry.command_roots)

	def arrange(self):
		self.help_messages.append(HelpMessage(
			None,
			'!!MCDR',
			self.plugin_manager.mcdr_server.tr('plugin_registry.mcdr_help_message'),
			PermissionLevel.MCDR_CONTROL_LEVEL
		))
		self.help_messages.sort()
		for listeners in self.event_listeners.values():
			listeners.sort()

	def export_commands(self, exporter: Callable[[Literal], Any]):
		for node in self.command_roots:
			exporter(node)
