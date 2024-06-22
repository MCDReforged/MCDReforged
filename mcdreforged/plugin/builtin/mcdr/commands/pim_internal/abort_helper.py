import contextlib
import threading
from typing import Dict, Callable, Any


_CALLBACK = Callable[[], Any]


class AbortHelper:
	def __init__(self):
		self.__callbacks: Dict[int, _CALLBACK] = {}
		self.__aborted = False
		self.__id_counter = 0
		self.__lock = threading.Lock()

	def abort(self):
		with self.__lock:
			self.__aborted = True
			callbacks = list(self.__callbacks.values())

		for cb in callbacks:
			cb()

	def clear(self):
		with self.__lock:
			self.__aborted = False
			self.__id_counter = 0
			self.__callbacks.clear()

	def is_aborted(self) -> bool:
		return self.__aborted

	@contextlib.contextmanager
	def add_abort_callback(self, callback: _CALLBACK):
		with self.__lock:
			key = self.__id_counter
			self.__id_counter += 1
			self.__callbacks[key] = callback
		try:
			yield
		finally:
			self.__callbacks.pop(key)
