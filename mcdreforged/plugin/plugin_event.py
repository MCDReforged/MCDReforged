import abc
import dataclasses
import functools
import inspect
from typing import Dict, List, Callable, TYPE_CHECKING

from mcdreforged.utils import class_utils

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
		return class_utils.represent(self)


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


class _MCDRPluginEventStorage:
	""":meta private:"""
	EVENT_DICT: Dict[str, PluginEvent] = {}

	@classmethod
	def register(cls, event: MCDREvent):
		if event.id in cls.EVENT_DICT:
			raise KeyError(event.id)
		cls.EVENT_DICT[event.id] = event


class MCDRPluginEvents:
	"""
	A collection of all possible :class:`MCDREvent` objects used in MCDR
	"""
	GENERAL_INFO = MCDREvent('mcdr.general_info', 'on_info')
	USER_INFO = MCDREvent('mcdr.user_info', 'on_user_info')

	SERVER_START_PRE = MCDREvent('mcdr.server_start_pre', 'on_server_start_pre')
	SERVER_START = MCDREvent('mcdr.server_start', 'on_server_start')
	SERVER_STARTUP = MCDREvent('mcdr.server_startup', 'on_server_startup')
	SERVER_STOP = MCDREvent('mcdr.server_stop', 'on_server_stop')

	MCDR_START = MCDREvent('mcdr.mcdr_start', 'on_mcdr_start')
	MCDR_STOP = MCDREvent('mcdr.mcdr_stop', 'on_mcdr_stop')

	PLAYER_JOINED = MCDREvent('mcdr.player_joined', 'on_player_joined')
	PLAYER_LEFT = MCDREvent('mcdr.player_left', 'on_player_left')

	PLUGIN_LOADED = MCDREvent('mcdr.plugin_loaded', 'on_load')
	PLUGIN_UNLOADED = MCDREvent('mcdr.plugin_unloaded', 'on_unload')

	@classmethod
	def get_event_list(cls) -> List[PluginEvent]:
		""":meta private:"""
		return list(_MCDRPluginEventStorage.EVENT_DICT.values())

	@classmethod
	def contains_id(cls, event_id: str) -> bool:
		""":meta private:"""
		return event_id in _MCDRPluginEventStorage.EVENT_DICT


def __register_mcdr_events():
	for name, value in vars(MCDRPluginEvents).items():
		if not name.startswith('_') and isinstance(value, MCDREvent):
			_MCDRPluginEventStorage.register(value)


__register_mcdr_events()


@dataclasses.dataclass(frozen=True)
class EventListener:
	plugin: 'AbstractPlugin'
	callback: Callable
	priority: int

	@functools.cached_property
	def is_async(self) -> bool:
		return inspect.iscoroutinefunction(self.callback)

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.priority < other.priority

	def __repr__(self):
		return class_utils.represent(self, {
			'plugin': self.plugin.get_name(),
			'callback': self.callback,
			'priority': self.priority,
		})
