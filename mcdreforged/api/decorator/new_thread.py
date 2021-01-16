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


def test():
	@new_thread()
	def bla1(value):
		time.sleep(0.5)
		print(threading.current_thread().getName() + ' ' + str(value))

	@new_thread
	def bla2(value):
		time.sleep(0.5)
		print(threading.current_thread().getName() + ' ' + str(value))

	@new_thread('awa')
	def bla3(value):
		time.sleep(0.5)
		print(threading.current_thread().getName() + ' ' + str(value))

	print(bla1, bla1('1'), inspect.getfullargspec(bla1))
	print(bla2, bla2('2'), inspect.getfullargspec(bla2))
	print(bla3, bla3('3'), inspect.getfullargspec(bla3))
	time.sleep(1)


if __name__ == '__main__':
	test()
