from threading import Thread, current_thread, Lock
from typing import Dict, Optional, Any


class ThreadLocalStorage:
	def __init__(self):
		self.__storage = {}  # type: Dict[Thread, Dict]
		self.__lock = Lock()

	def __get_dict(self, thread: Thread):
		if thread not in self.__storage:
			self.__storage[thread] = {}
		return self.__storage[thread]

	def get(self, key: Any, default=None, *, thread: Optional[Thread] = None):
		if thread is None:
			thread = current_thread()
		with self.__lock:
			return self.__get_dict(thread).get(key, default)

	def put(self, key: Any, value: Any, *, thread: Optional[Thread] = None):
		if thread is None:
			thread = current_thread()
		with self.__lock:
			self.__get_dict(thread)[key] = value

	def pop(self, key, *, thread: Optional[Thread] = None) -> Optional[Any]:
		if thread is None:
			thread = current_thread()
		with self.__lock:
			dt = self.__get_dict(thread)
			if key in dt:
				return dt.pop(key)
			else:
				return None
