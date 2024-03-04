from typing import Callable, Union, Optional

from mcdreforged.plugin.plugin_event import PluginEvent
from mcdreforged.plugin.si.server_interface import ServerInterface

__all__ = [
	'event_listener'
]


def event_listener(event: Union[PluginEvent, str], *, priority: Optional[int] = None):
	"""
	This decorator is used to register a custom event listener without involving
	:meth:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface.register_event_listener`

	It accepts a single str or :class:`~mcdreforged.plugin.plugin_event.PluginEvent`
	indicating the event you are listening to as parameter,
	and will register the function as the callback of the given listener

	It's highly suggested to use this decorator only in the :ref:`entry point <plugin-entrypoint>` of your plugin,
	so it can work correctly and register the event listener in the correct time
	
	Example::
	
		@event_listener(MCDRPluginEvents.GENERAL_INFO)
		def my_on_info(server, info):
			server.logger.info('on info in my own listener')

	The above example is equivalent to::

		def on_load(server, old):
			server.register_event_listener(MCDRPluginEvents.GENERAL_INFO, my_on_info)

	:param event: The event to register a listener
	:keyword priority: Optional, the priority of the event listener
	:raise TypeError: If given *event* is invalid
	:raise RuntimeError: If it fails to acquire a :class:`~mcdreforged.plugin.si.plugin_server_interface.PluginServerInterface`
		(see :meth:`~mcdreforged.plugin.si.server_interface.ServerInterface.as_plugin_server_interface` for more details)
	"""
	def wrapper(callback: Callable) -> Callable:
		ServerInterface.psi().register_event_listener(event, callback, priority)
		return callback

	if not isinstance(event, (PluginEvent, str)):
		raise TypeError('An event parameter is required')
	return wrapper
