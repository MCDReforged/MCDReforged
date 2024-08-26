import contextlib
from contextvars import ContextVar
from threading import Thread, current_thread
from typing import Dict, Generic, TypeVar, Union

_T = TypeVar('_T')
_V = TypeVar('_V')


class _None:
	pass


_NONE = _None()


class ThreadLocalStorage(Generic[_V]):
	"""
	Stored values should be immutable, cuz it might be shared between coroutines
	"""
	def __init__(self):
		self.__storage: Dict[Thread, _V] = {}

		# NOTES: its lifecycle is beyond this object, but it's fine cuz tls is only used in singleton
		# see python docs for ContextVar
		self.__context_var: ContextVar[Union[_V, _None]] = ContextVar('tls', default=_NONE)

	def __cleanup_storage(self, thread: Thread):
		if not thread.is_alive():
			with contextlib.suppress(KeyError):
				self.__storage.pop(thread)

	def get(self, *, default: _T) -> Union[_V, _T]:
		value = self.__context_var.get(default)
		if isinstance(value, _None):
			if value != _NONE:
				print(id(value), id(_NONE))
			return default
		return value

	def get_by_thread(self, thread: Thread, default: _T) -> Union[_V, _T]:
		return self.__storage.get(thread, default)

	def put(self, value: _V):
		self.__storage[current_thread()] = value
		self.__context_var.set(value)

	def pop(self):
		with contextlib.suppress(KeyError):
			self.__storage.pop(current_thread())
		self.__context_var.set(_NONE)
