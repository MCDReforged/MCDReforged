from threading import Thread, current_thread, Lock
from typing import Dict, Optional, Generic, TypeVar

_K = TypeVar('_K')
_V = TypeVar('_V')


class ThreadLocalStorage(Generic[_K, _V]):
	def __init__(self):
		self.__storage: Dict[Thread, Dict[_K, _V]] = {}
		self.__lock = Lock()

	def __get_dict(self, thread: Thread) -> Dict[_K, _V]:
		if thread not in self.__storage:
			self.__storage[thread] = {}
		return self.__storage[thread]

	def get(self, key: _K, default=None, *, thread: Optional[Thread] = None) -> Optional[_V]:
		if thread is None:
			thread = current_thread()
		with self.__lock:
			return self.__get_dict(thread).get(key, default)

	def put(self, key: _K, value: _V, *, thread: Optional[Thread] = None):
		if thread is None:
			thread = current_thread()
		with self.__lock:
			self.__get_dict(thread)[key] = value

	def pop(self, key: _K, *, thread: Optional[Thread] = None) -> Optional[_V]:
		if thread is None:
			thread = current_thread()
		with self.__lock:
			dt = self.__get_dict(thread)
			if key in dt:
				return dt.pop(key)
			else:
				return None
