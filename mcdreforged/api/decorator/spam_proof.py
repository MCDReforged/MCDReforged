import functools
from threading import RLock
from typing import Callable

from mcdreforged.utils import misc_util

__all__ = [
	'spam_proof'
]


def spam_proof(arg=None, *, lock_class=RLock):
	"""
	Use a lock to protect the decorated function from being invoked on multiple threads at the same time
	If a multiple-invocation happens, only the first invocation can be executed normally, other invocations
	will be skipped
	The type of the lock can be specified with the `lock_class` parameter, for example
	it can be `threading.RLock` (default) or `threading.Lock`

	The return value of the decorated function is modified into a bool, indicating if this invocation is executed normally
	The decorated function has 2 extra fields:
	- `original` field: stores the original undecorated function
	- `lock` field: stores the lock object used in the spam proof logic
	"""
	def wrapper(func):
		@functools.wraps(func)  # to preserve the origin function information
		def wrap(*args, **kwargs):
			acquired = lock.acquire(blocking=False)
			if acquired:
				try:
					func(*args, **kwargs)
				finally:
					lock.release()
			return acquired
		misc_util.copy_signature(wrap, func)
		lock = lock_class()
		wrap.original = func
		wrap.lock = lock
		return wrap
	# Directly use @spam_proof without ending brackets case
	if isinstance(arg, Callable):
		return wrapper(arg)
	# Use @spam_proof with ending brackets case
	else:
		return wrapper
