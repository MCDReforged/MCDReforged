import contextlib
import functools
import inspect
import sys
from abc import ABC, abstractmethod
from types import MethodType
from typing import Callable, TypeVar, Generic, Coroutine, Iterable, TYPE_CHECKING

from typing_extensions import override

if TYPE_CHECKING:
	from mcdreforged.command.builder.common import CommandContext


class CallbackError(Exception):
	Builder = Callable[[Exception], 'CallbackError']

	def __init__(self, exception: Exception, context: 'CommandContext', action: str):
		self.exception = exception
		self.context = context.copy()
		self.action = action
		self.exc_info = sys.exc_info()

	@classmethod
	def builder(cls, context: 'CommandContext', action: str) -> Builder:
		return functools.partial(cls, context=context, action=action)


_T = TypeVar('_T')


class CallbackInvoker(ABC):
	@abstractmethod
	def invoke_sync(self, func: Callable[..., _T], args: Iterable):
		raise NotImplementedError()

	@abstractmethod
	def invoke_async(self, func: Callable[..., Coroutine], args: Iterable):
		raise NotImplementedError()


class DirectCallbackInvoker(CallbackInvoker):
	@override
	def invoke_sync(self, func: Callable[..., _T], args: Iterable) -> _T:
		return func(*args)

	@override
	def invoke_async(self, func: Callable[..., Coroutine], args: Iterable):
		raise RuntimeError(f'Async callback is not supported, func: {func}')


class ScheduledCallback(Generic[_T]):
	def __init__(self, callback: Callable[..., _T], args: tuple, error_factory: CallbackError.Builder):
		self.__callback = callback
		self.__args = args
		self.__error_factory = error_factory

	@contextlib.contextmanager
	def wrap_callback_error(self):
		try:
			yield
		except Exception as e:
			raise self.__error_factory(e)

	def invoke(self, invoker: CallbackInvoker):
		spec_args = inspect.getfullargspec(self.__callback).args
		spec_args_len = len(spec_args)

		real_func = self.__callback
		for i in range(100):  # found the real function for the MethodType check
			if isinstance(real_func, functools.partial):
				real_func = real_func.func
			else:
				break
		if isinstance(real_func, MethodType):  # class method, remove the 1st param
			spec_args_len -= 1
		call_args = self.__args[:spec_args_len]

		with self.wrap_callback_error():
			if inspect.iscoroutinefunction(self.__callback):
				return invoker.invoke_async(self.__callback, call_args)
			else:
				return invoker.invoke_sync(self.__callback, call_args)
