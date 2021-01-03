from typing import Dict, List

from mcdr.permission_manager import PermissionLevel
from mcdr.plugin.plugin_event import EventListener
from mcdr.rtext import RTextBase

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


class PluginRegistry:
	def __init__(self, plugin):
		self.plugin = plugin
		self.event_listeners = {}  # type: Dict[str, List[EventListener]]
		self.help_messages = []

	def register_help_message(self, help_message: HelpMessage):
		self.help_messages.append(help_message)

	def register_listener(self, event_id: str, listener: EventListener):
		listeners = self.event_listeners.get(event_id, [])
		listeners.append(listener)
		self.event_listeners[event_id] = listeners

	def register_command(self):
		pass  # TODO

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()


class PluginManagerRegistry:
	def __init__(self, plugin_manager):
		self.plugin_manager = plugin_manager
		self.event_listeners = {}  # type: Dict[str, List[EventListener]]
		self.help_messages = []  # type: List[HelpMessage]

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()

	def collect(self, registry: PluginRegistry):
		for event_id, plg_listeners in registry.event_listeners.items():
			listeners = self.event_listeners.get(event_id, [])
			listeners.extend(plg_listeners)
			self.event_listeners[event_id] = listeners
		self.help_messages.extend(registry.help_messages)

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
