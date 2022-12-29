from enum import Enum, auto
from threading import RLock
from typing import Generic, TypeVar, Callable, Any

T = TypeVar('T')


class _State(Enum):
	PENDING = auto()
	FINISHED = auto()


class Future(Generic[T]):
	_NONE = object()

	def __init__(self):
		self.__value = self._NONE
		self.__state = _State.PENDING
		self.__lock = RLock()
		self.__done_callbacks = []

	def __invoke_callbacks(self, value: T):
		for callback in self.__done_callbacks:
			try:
				callback(value)
			except:
				pass  # TODO: expose the exception

	def set_result(self, value: T):
		"""
		Called by the supplier
		"""
		with self.__lock:
			self.__value = value
			self.__state = _State.FINISHED
		self.__invoke_callbacks(value)

	def is_finished(self):
		return self.__state == _State.FINISHED

	def get(self) -> T:
		if self.__value is not self._NONE:
			return self.__value
		else:
			raise

	def add_done_callback(self, callback: Callable[[T], Any]):
		with self.__lock:
			if self.is_finished():
				callback(self.get())
			else:
				self.__done_callbacks.append(callback)