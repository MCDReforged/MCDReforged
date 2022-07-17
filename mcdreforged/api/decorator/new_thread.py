import functools
import threading
from typing import Optional, Callable, Union

__all__ = [
	'new_thread',
	'FunctionThread'
]

from mcdreforged.utils import misc_util


class FunctionThread(threading.Thread):
	__NONE = object()

	def __init__(self, target, name, args, kwargs):
		super().__init__(target=target, args=args, kwargs=kwargs, name=name, daemon=True)
		self.__return_value = self.__NONE
		self.__error = None

		def wrapped_target(*args_, **kwargs_):
			try:
				self.__return_value = target(*args_, **kwargs_)
			except Exception as e:
				self.__error = e
				raise e from None

		self._target = wrapped_target

	def get_return_value(self, block: bool = False, timeout: Optional[float] = None):
		if block:
			self.join(timeout)
		if self.__return_value is self.__NONE:
			if self.is_alive():
				raise RuntimeError('The thread is still running')
			raise self.__error
		return self.__return_value


def new_thread(arg: Optional[Union[str, Callable]] = None):
	"""
	Use a new thread to execute the decorated function asynchronously
	The name of the thread can be specified in parameter

	The return value of the decorated function is changed to the thread instance that executes this function
	The decorated function has 1 extra field:
	- `original` field: stores the original undecorated function
	"""
	def wrapper(func):
		@functools.wraps(func)  # to preserve the origin function information
		def wrap(*args, **kwargs):
			thread = FunctionThread(target=func, args=args, kwargs=kwargs, name=thread_name)
			thread.start()
			return thread
		# bring the signature of the func to the wrap function
		# so inspect.getfullargspec(func) works correctly
		misc_util.copy_signature(wrap, func)
		wrap.original = func  # access this field to get the original function
		return wrap
	# Directly use @new_thread without ending brackets case, e.g. @new_thread
	if isinstance(arg, Callable):
		thread_name = None
		return wrapper(arg)
	# Use @new_thread with ending brackets case, e.g. @new_thread('A'), @new_thread()
	else:
		thread_name = arg
		return wrapper

