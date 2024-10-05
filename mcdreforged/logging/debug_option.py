from enum import Flag, auto


class DebugOption(Flag):
	"""
	Remember to sync with the "debug" option in the default config file
	"""
	mask: int

	ALL = auto()
	MCDR = auto()
	HANDLER = auto()
	REACTOR = auto()
	PLUGIN = auto()
	PERMISSION = auto()
	COMMAND = auto()
	TASK_EXECUTOR = auto()


def __pre_fetch_debug_option_value():
	"""
	DebugOption.value call is more costly than simple attribute access
	"""
	for option in DebugOption:
		option.mask = option.value


__pre_fetch_debug_option_value()
