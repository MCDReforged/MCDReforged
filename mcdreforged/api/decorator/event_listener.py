import threading
from typing import Callable, Union, Optional

from mcdreforged.plugin.plugin_event import PluginEvent
from mcdreforged.plugin.server_interface import ServerInterface

__all__ = [
	'event_listener'
]


def event_listener(event: Union[PluginEvent, str], *, priority: Optional[int] = None):
	"""
	Use a new thread to execute the decorated function
	The function return value will be set to the thread instance that executes this function
	The name of the thread can be specified in parameter
	"""
	def wrapper(callback: Callable):
		server = ServerInterface.get_instance().as_plugin_server_interface()
		if server is None:
			raise RuntimeError('Cannot get current executing plugin, current thread: {}'.format(threading.current_thread()))
		server.register_event_listener(event, callback, priority)
		return callback

	if not isinstance(event, (PluginEvent, str)):
		raise TypeError('An event parameter is required')
	return wrapper
