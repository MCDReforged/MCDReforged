import functools
import inspect
import threading
import time
from typing import Optional, Callable


def new_thread(thread_name: Optional[str or Callable] = None):
	"""
	Use a new thread to execute the decorated function
	The function return value will be set to the thread instance that executes this function
	The name of the thread can be specified in parameter
	"""
	def wrapper(func):
		@functools.wraps(func)  # to preserve the origin function information
		def wrap(*args, **kwargs):
			thread = threading.Thread(target=func, args=args, kwargs=kwargs, name=thread_name)
			thread.setDaemon(True)
			thread.start()
			return thread
		# bring the signature of the func to the wrap function
		# so inspect.getfullargspec(func) works correctly
		# https://stackoverflow.com/questions/39926567find/python-create-decorator-preserving-function-arguments
		wrap.__signature__ = inspect.signature(func)
		return wrap
	# Directly use @on_new_thread without ending brackets case
	if isinstance(thread_name, Callable):
		this_is_a_function = thread_name
		thread_name = None
		return wrapper(this_is_a_function)
	# Use @on_new_thread with ending brackets case
	return wrapper
