import abc
from typing import Dict, List, Callable, TYPE_CHECKING

from mcdreforged.utils import class_util

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class PluginEvent(abc.ABC):
	"""
	The abstract base class of plugin event

	A plugin event has an :attr:`id` field as its identifier
	"""
	def __init__(self, event_id: str):
		"""
		:param event_id: The id of the plugin event
		"""
		self.id: str = event_id
		"""The id of the plugin event"""

	def __repr__(self):
		return class_util.represent(self)


class LiteralEvent(PluginEvent):
	"""
	A simple and minimum implementation of :class:`PluginEvent`

	All information you need to construct a :class:`LiteralEvent` object is only the event id
	"""
	def __init__(self, event_id: str):
		"""
		Create a :class:`LiteralEvent`

		:param event_id: The id of the plugin event
		"""
		super().__init__(event_id)


class MCDREvent(PluginEvent):
	"""
	Plugin event that used in MCDR

	Generally, only MCDR is supposed to construct :class:`MCDREvent`
	"""
	def __init__(self, event_id: str, default_method_name: str):
		super().__init__(event_id)
		self.default_method_name = default_method_name


class _PluginEventStorage:
	EVENT_DICT = {}  # type: Dict[str, PluginEvent]

	@classmethod
	def register(cls, event: MCDREvent):
		cls.EVENT_DICT[event.id] = event
		return event

	@classmethod
	def get_event_list(cls) -> List[PluginEvent]:
		return list(cls.EVENT_DICT.values())


class MCDRPluginEvents:
	"""
	A collection of all possible :class:`MCDREvent` objects used in MCDR
	"""
	GENERAL_INFO 	= _PluginEventStorage.register(MCDREvent('mcdr.general_info', 'on_info'))
	USER_INFO 		= _PluginEventStorage.register(MCDREvent('mcdr.user_info', 'on_user_info'))
	SERVER_START 	= _PluginEventStorage.register(MCDREvent('mcdr.server_start', 'on_server_start'))
	SERVER_STARTUP 	= _PluginEventStorage.register(MCDREvent('mcdr.server_startup', 'on_server_startup'))
	SERVER_STOP 	= _PluginEventStorage.register(MCDREvent('mcdr.server_stop', 'on_server_stop'))
	MCDR_START 		= _PluginEventStorage.register(MCDREvent('mcdr.mcdr_start', 'on_mcdr_start'))
	MCDR_STOP 		= _PluginEventStorage.register(MCDREvent('mcdr.mcdr_stop', 'on_mcdr_stop'))
	PLAYER_JOINED 	= _PluginEventStorage.register(MCDREvent('mcdr.player_joined', 'on_player_joined'))
	PLAYER_LEFT 	= _PluginEventStorage.register(MCDREvent('mcdr.player_left', 'on_player_left'))
	PLUGIN_LOADED 	= _PluginEventStorage.register(MCDREvent('mcdr.plugin_loaded', 'on_load'))
	PLUGIN_UNLOADED = _PluginEventStorage.register(MCDREvent('mcdr.plugin_unloaded', 'on_unload'))
	# PLUGIN_REMOVED 	= _PluginEventStorage.register(MCDREvent('mcdr.plugin_removed',  'on_remove'))

	@classmethod
	def get_event_list(cls):
		""":meta private:"""
		return _PluginEventStorage.get_event_list()

	@classmethod
	def contains_id(cls, event_id: str):
		""":meta private:"""
		return event_id in _PluginEventStorage.EVENT_DICT


class EventListener:
	def __init__(self, plugin: 'AbstractPlugin', callback: Callable, priority: int):
		self.plugin = plugin
		self.callback = callback
		self.priority = priority

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.priority < other.priority

	def execute(self, *args, **kwargs):
		return self.callback(*args, **kwargs)

	def __repr__(self):
		return 'EventListener[plugin={},priority={},callback={}]'.format(self.plugin.get_name(), self.priority, self.callback)
