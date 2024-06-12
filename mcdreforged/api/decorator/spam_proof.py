import functools
from threading import RLock
from typing import Callable, Optional

from mcdreforged.utils import misc_utils

__all__ = [
	'spam_proof'
]


def spam_proof(arg=None, *, lock_class=RLock, skip_callback: Optional[Callable] = None):
	"""
	Use a lock to protect the decorated function from being invoked on multiple threads at the same time

	If a multiple-invocation happens, only the first invocation can be executed normally, other invocations
	will be skipped

	The return value of the decorated function is modified into a bool, indicating if this invocation is executed normally

	The decorated function has 2 extra fields:

	- ``original`` field: stores the original undecorated function
	- ``lock`` field: stores the lock object used in the spam proof logic

	Example::

		@spam_proof
		def some_work(value):
			# doing some important logics
			foo = value

	The above example is equivalent to::

		lock = threading.RLock()

		def some_work(value) -> bool:
			acquired = lock.acquire(blocking=False)
			if acquired:
				try:
					# doing some not thread-safe logics
					foo = value
				finally:
					lock.release()
			return acquired

	:keyword lock_class: The type of the lock. It can be :class:`threading.Lock` or :class:`threading.RLock` (default)
	:keyword skip_callback: (optional) The callback function that will be invoked with all parameters of the decorated function
		when the invocation is skipped

	Keyword ``skip_callback`` example::

		>>> def my_callback(value):
		...     print('skip', value)

		>>> @spam_proof(skip_callback=my_callback)
		... def some_work(value):
		...     event.wait()

		>>> def threaded_invoke():
		... 	print(some_work(0.1))  # invocation normal

		>>> from threading import Thread, Event
		>>> t, event = Thread(target=threaded_invoke), Event()
		>>> t.start()
		>>> some_work(123)  # invocation skipped
		skip 123
		False
		>>> _ = event.set(), t.join()
		True

	.. versionadded:: v2.5.0
	.. versionadded:: v2.7.0
		Added ``skip_callback`` keyword argument
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
			else:
				if skip_callback is not None:
					skip_callback(*args, **kwargs)
			return acquired
		misc_utils.copy_signature(wrap, func)
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
