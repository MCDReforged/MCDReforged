import abc
from typing import Dict, List, Callable, TYPE_CHECKING

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin import AbstractPlugin


class PluginEvent(abc.ABC):
	def __init__(self, event_id: str):
		self.id = event_id


class LiteralEvent(PluginEvent):
	def __init__(self, event_id: str):
		super().__init__(event_id)

	def __repr__(self):
		return 'LiteralEvent[id={}]'.format(self.id)


class MCDREvent(PluginEvent):
	def __init__(self, event_id: str, name: str, default_method_name: str):
		super().__init__(event_id)
		self.name = name
		self.default_method_name = default_method_name

	def __repr__(self):
		return 'MCDREvent[name={}]'.format(self.name)


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
	GENERAL_INFO 	= _PluginEventStorage.register(MCDREvent('mcdr.general_info', 'General info', 'on_info'))
	USER_INFO 		= _PluginEventStorage.register(MCDREvent('mcdr.user_info', 'User info', 'on_user_info'))
	SERVER_START 	= _PluginEventStorage.register(MCDREvent('mcdr.server_start', 'Server start', 'on_server_start'))
	SERVER_STARTUP 	= _PluginEventStorage.register(MCDREvent('mcdr.server_startup', 'Server startup', 'on_server_startup'))
	SERVER_STOP 	= _PluginEventStorage.register(MCDREvent('mcdr.server_stop', 'Server startup', 'on_server_stop'))
	MCDR_START 		= _PluginEventStorage.register(MCDREvent('mcdr.mcdr_start', 'MCDR start', 'on_mcdr_start'))
	MCDR_STOP 		= _PluginEventStorage.register(MCDREvent('mcdr.mcdr_stop', 'MCDR stop', 'on_mcdr_stop'))
	PLAYER_JOINED 	= _PluginEventStorage.register(MCDREvent('mcdr.player_joined', 'Player joined', 'on_player_joined'))
	PLAYER_LEFT 	= _PluginEventStorage.register(MCDREvent('mcdr.player_left', 'Player left', 'on_player_left'))
	PLUGIN_LOADED 	= _PluginEventStorage.register(MCDREvent('mcdr.plugin_loaded', 'Plugin loaded', 'on_load'))
	PLUGIN_UNLOADED = _PluginEventStorage.register(MCDREvent('mcdr.plugin_unloaded', 'Plugin unloaded', 'on_unload'))
	PLUGIN_REMOVED 	= _PluginEventStorage.register(MCDREvent('mcdr.plugin_removed', 'Plugin removed', 'on_remove'))

	@classmethod
	def get_event_list(cls):
		return _PluginEventStorage.get_event_list()

	@classmethod
	def contains_id(cls, event_id: str):
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
