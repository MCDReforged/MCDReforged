from threading import Thread, current_thread, Lock
from typing import Dict, Optional


class ThreadLocalStorage:
	def __init__(self):
		self.__storage = {}  # type: Dict[Thread, Dict]
		self.__lock = Lock()

	def __get(self, thread: Thread):
		if thread not in self.__storage:
			self.__storage[thread] = {}
		return self.__storage[thread]

	def get(self, key, default=None, *, thread: Optional[Thread] = None):
		if thread is None:
			thread = current_thread()
		with self.__lock:
			return self.__get(thread).get(key, default)

	def put(self, key, value, *, thread: Optional[Thread] = None):
		if thread is None:
			thread = current_thread()
		with self.__lock:
			self.__get(thread)[key] = value

