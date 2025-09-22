import functools
import threading
from typing import Optional, Callable, Union, TypeVar, Iterable, overload, Generic, Any

from typing_extensions import ParamSpec

from mcdreforged.utils import misc_utils

__all__ = [
	'new_thread',
	'FunctionThread'
]


_T = TypeVar('_T')
_P = ParamSpec('_P')


class FunctionThread(threading.Thread, Generic[_T]):
	"""
	A Thread subclass which is used in decorator :func:`new_thread` to wrap a synchronized function call
	"""
	__NONE: Any = object()

	def __init__(self, target: Callable[..., _T], name: Optional[str], args: Iterable = (), kwargs: Optional[dict] = None):
		super().__init__(target=target, args=args, kwargs=kwargs, name=name, daemon=True)
		self.__return_value: _T = self.__NONE
		self.__error: Optional[Exception] = None

		def wrapped_target(*args_, **kwargs_):
			try:
				self.__return_value = target(*args_, **kwargs_)
			except Exception as e:
				self.__error = e
				raise e from None

		self._target = wrapped_target

	def get_return_value(self, block: bool = False, timeout: Optional[float] = None) -> _T:
		"""
		Get the return value of the original function

		If an exception has occurred during the original function call, the exception will be risen again here

		Examples::

			>>> import time
			>>> @new_thread
			... def do_something(text: str):
			... 	time.sleep(1)
			... 	return text

			>>> do_something('task').get_return_value(block=True)
			'task'

		:param block: If it should join the thread before getting the return value to make sure the function invocation finishes
		:param timeout: The maximum timeout for the thread join
		:raise RuntimeError: If the thread is still alive when getting return value. Might be caused by ``block=False``
			while the thread is still running, or thread join operation times out
		:return: The return value of the original function
		"""
		if block:
			self.join(timeout)
		if self.__return_value is self.__NONE:
			if self.is_alive():
				raise RuntimeError('The thread is still running')
			if self.__error is None:
				raise AssertionError()
			raise self.__error
		return self.__return_value


@overload
def new_thread() -> Callable[[Callable[_P, _T]], Callable[_P, FunctionThread]]:
	...


@overload
def new_thread(thread_name: str, /) -> Callable[[Callable[_P, _T]], Callable[_P, FunctionThread]]:
	...


@overload
def new_thread(func: Callable[_P, _T], /) -> Callable[_P, FunctionThread]:
	...


def new_thread(arg: Optional[Union[str, Callable[_P, _T]]] = None, /):
	"""
	This is a one line solution to make your function executes in parallels.
	When decorated with this decorator, functions will be executed in a new daemon thread

	This decorator only changes the return value of the function to the created ``Thread`` object.
	Beside the return value, it reserves all signatures of the decorated function,
	so you can safely use the decorated function as if there's no decorating at all

	It's also a simple compatible upgrade method for old MCDR 0.x plugins

	The return value of the decorated function is changed to the ``Thread`` object that executes this function

	The decorated function has 1 extra field:

	* ``original`` field: The original undecorated function
	
	Examples::

		>>> import time

		>>> @new_thread('My Plugin Thread')
		... def do_something(text: str):
		... 	time.sleep(1)
		... 	print(threading.current_thread().name)
		>>> callable(do_something.original)
		True
		>>> t = do_something('foo')
		>>> isinstance(t, FunctionThread)
		True
		>>> t.join()
		My Plugin Thread

	:param arg: A :class:`str`, the name of the thread. It's recommend to specify the thread name, so when you
		log something by ``server.logger``, a meaningful thread name will be displayed
		instead of a plain and meaningless ``Thread-3``
	"""
	def wrapper(func: Callable[_P, _T]) -> Callable[_P, FunctionThread]:
		@functools.wraps(func)  # to preserve the origin function information
		def wrap(*args: _P.args, **kwargs: _P.kwargs) -> FunctionThread:
			thread = FunctionThread(target=func, args=args, kwargs=kwargs, name=thread_name)
			thread.start()
			return thread
		# bring the signature of the func to the wrap function
		# so inspect.getfullargspec(func) works correctly
		misc_utils.copy_signature(wrap, func)
		# access this field to get the original function
		wrap.original = func  # type: ignore
		return wrap

	thread_name: Optional[str]
	# Directly use @new_thread without ending brackets case, e.g. @new_thread
	if arg is not None and callable(arg):
		thread_name = None
		return wrapper(arg)
	# Use @new_thread with ending brackets case, e.g. @new_thread('A'), @new_thread()
	else:
		thread_name = arg
		return wrapper
