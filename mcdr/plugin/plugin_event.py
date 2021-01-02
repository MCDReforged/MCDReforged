from typing import List


class PluginEvent:
	def __init__(self, event_id, name):
		self.id = event_id
		self.name = name

	def __repr__(self):
		return 'PluginEvent[{}]'.format(self.name)


class LegacyPluginEvent(PluginEvent):
	def __init__(self, event_id, name, legacy_method_name):
		super().__init__(event_id, name)
		self.legacy_method_name = legacy_method_name


class PluginEventStorage:
	__EVENT_LIST = []  # type: List[PluginEvent]

	@classmethod
	def register(cls, event: PluginEvent):
		cls.__EVENT_LIST.append(event)
		return event

	@classmethod
	def get_event_list(cls):
		return cls.__EVENT_LIST


class PluginEvents:
	GENERAL_INFO 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.general_info', 'General info', 'on_info'))
	USER_INFO 		= PluginEventStorage.register(LegacyPluginEvent('mcdr.user_info', 'User info', 'on_user_info'))
	SERVER_STARTUP 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.server_startup', 'Server startup', 'on_server_startup'))
	SERVER_STOP 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.server_stop', 'Server startup', 'on_server_stop'))
	MCDR_STOP 		= PluginEventStorage.register(LegacyPluginEvent('mcdr.mcdr_stop', 'MCDR stop', 'on_mcdr_stop'))
	PLAYER_JOIN 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.player_join', 'Player joined', 'on_player_joined'))
	PLAYER_LEFT 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.player_left', 'Player left', 'on_player_left'))
	PLUGIN_LOAD 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.on_plugin_load', 'Plugin loaded', 'on_load'))
	PLUGIN_UNLOAD 	= PluginEventStorage.register(LegacyPluginEvent('mcdr.on_plugin_unload', 'Plugin unloaded', 'on_unload'))

	@classmethod
	def get_event_list(cls):
		return PluginEventStorage.get_event_list()
