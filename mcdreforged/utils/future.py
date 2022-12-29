from threading import RLock
from typing import Generic, TypeVar, Callable, Any

T = TypeVar('T')


class Future(Generic[T]):
	_NONE = object()

	def __init__(self):
		self.__value = self._NONE
		self.__lock = RLock()
		self.__done_callbacks = []

	@classmethod
	def completed(cls, value: T) -> 'Future[T]':
		future = Future()
		future.set_result(value)
		return future

	def __invoke_callbacks(self, value: T):
		with self.__lock:
			callbacks = self.__done_callbacks.copy()
			self.__done_callbacks.clear()
		for callback in callbacks:
			callback(value)

	def set_result(self, value: T):
		"""
		Called by the supplier
		"""
		with self.__lock:
			self.__value = value
		self.__invoke_callbacks(value)

	def is_finished(self):
		return self.__value is not self._NONE

	def get(self) -> T:
		if self.__value is not self._NONE:
			return self.__value
		else:
			raise ValueError('Future is not finished yet')

	def add_done_callback(self, callback: Callable[[T], Any]):
		with self.__lock:
			if not self.is_finished():
				self.__done_callbacks.append(callback)
				return
		callback(self.get())
