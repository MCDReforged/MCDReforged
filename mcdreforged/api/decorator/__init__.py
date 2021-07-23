"""
Some useful decorators
"""
from .event_listener import event_listener
from .new_thread import new_thread, FunctionThread

__all__ = [
	'new_thread', 'FunctionThread',
	'event_listener'
]
