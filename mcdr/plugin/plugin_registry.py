import collections
from typing import Dict, Set, Callable

from mcdr.plugin.plugin_event import PluginEvent
from mcdr.rtext import RTextBase

HelpMessage = collections.namedtuple('HelpMessage', 'prefix message plugin_name')


class PluginRegistry:
	def __init__(self, plugin):
		self.plugin = plugin
		self.event_listeners = {}  # type: Dict[PluginEvent, Set[Callable]]
		self.help_messages = []

	def register_help_message(self, prefix: str, help_message: RTextBase):
		self.help_messages.append(HelpMessage(prefix, help_message, self.plugin.get_name()))

	def register_listener(self, event: PluginEvent or str, callback: Callable):
		listeners = self.event_listeners.get(event, set())
		listeners.add(callback)
		self.event_listeners[event] = listeners

	def register_command(self):
		pass  # TODO

	def clear(self):
		self.event_listeners.clear()
		self.help_messages.clear()
