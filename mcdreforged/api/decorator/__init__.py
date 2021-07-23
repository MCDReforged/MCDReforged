"""
Some useful decorators
"""
from .event_listener import event_listener
from .new_thread import new_thread

__all__ = [
	'new_thread',
	'event_listener'
]
