"""
Some useful decorators
"""
from .event_listener import event_listener
from .new_thread import new_thread, FunctionThread
from .spam_proof import spam_proof

__all__ = [
	'event_listener',
	'new_thread', 'FunctionThread',
	'spam_proof',
]
