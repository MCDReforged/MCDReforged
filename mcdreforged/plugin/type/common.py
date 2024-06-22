import enum


class PluginState(enum.Enum):
	UNINITIALIZED = enum.auto()  # just created the instance
	LOADING = enum.auto()        # loading the .py entrance file / metadata of a multi-file plugin
	LOADED = enum.auto()         # loaded the .py entrance file / metadata of a multi-file plugin
	READY = enum.auto()          # registered module & default listeners & translations, now it's ready to do anything
	UNLOADING = enum.auto()      # just removed from the plugin list, ready to call "on unload" event
	UNLOADED = enum.auto()       # unloaded, should never access it


class PluginType(enum.Enum):
	"""
	:doc:`Format of the plugin </plugin_dev/plugin_format>`

	.. versionadded:: v2.13.0
	"""

	builtin = enum.auto()
	"""MCDR builtin plugin"""

	solo = enum.auto()
	""":ref:`plugin_dev/plugin_format:Solo Plugin`"""

	packed = enum.auto()
	""":ref:`plugin_dev/plugin_format:Packed Plugin`"""

	directory = enum.auto()
	""":ref:`plugin_dev/plugin_format:Directory Plugin`"""

	linked_directory = enum.auto()
	""":ref:`plugin_dev/plugin_format:Linked Directory Plugin`"""
