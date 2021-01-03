from typing import Dict, List


class PluginEvent:
	def __init__(self, event_id: str, name: str, default_method_name: str):
		self.id = event_id
		self.name = name
		self.default_method_name = default_method_name

	def __repr__(self):
		return 'PluginEvent[{}]'.format(self.name)


class _PluginEventStorage:
	EVENT_DICT = {}  # type: Dict[str, PluginEvent]

	@classmethod
	def register(cls, event: PluginEvent):
		cls.EVENT_DICT[event.id] = event
		return event

	@classmethod
	def get_event_list(cls) -> List[PluginEvent]:
		return list(cls.EVENT_DICT.values())


class PluginEvents:
	# legacy events
	GENERAL_INFO 	= _PluginEventStorage.register(PluginEvent('mcdr.general_info', 'General info', 'on_info'))
	USER_INFO 		= _PluginEventStorage.register(PluginEvent('mcdr.user_info', 'User info', 'on_user_info'))
	SERVER_STARTUP 	= _PluginEventStorage.register(PluginEvent('mcdr.server_startup', 'Server startup', 'on_server_startup'))
	SERVER_STOP 	= _PluginEventStorage.register(PluginEvent('mcdr.server_stop', 'Server startup', 'on_server_stop'))
	MCDR_STOP 		= _PluginEventStorage.register(PluginEvent('mcdr.mcdr_stop', 'MCDR stop', 'on_mcdr_stop'))
	PLAYER_JOIN 	= _PluginEventStorage.register(PluginEvent('mcdr.player_join', 'Player joined', 'on_player_joined'))
	PLAYER_LEFT 	= _PluginEventStorage.register(PluginEvent('mcdr.player_left', 'Player left', 'on_player_left'))
	PLUGIN_LOAD 	= _PluginEventStorage.register(PluginEvent('mcdr.plugin_load', 'Plugin loaded', 'on_load'))
	PLUGIN_UNLOAD 	= _PluginEventStorage.register(PluginEvent('mcdr.plugin_unload', 'Plugin unloaded', 'on_unload'))

	USER_COMMAND	= _PluginEventStorage.register(PluginEvent('mcdr.on', 'User enter command', 'on_command'))

	@classmethod
	def get_event_list(cls):
		return _PluginEventStorage.get_event_list()
