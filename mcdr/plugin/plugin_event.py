import collections

Event = collections.namedtuple('Event', 'id default_method')


class PluginEvent:
	ON_PLUGIN_LOAD = Event('mcdr.on_plugin_load', 'on_load')
	ON_PLUGIN_UNLOAD = Event('mcdr.on_plugin_unload', 'on_unload')
