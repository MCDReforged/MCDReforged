import enum
import threading


class ConfirmHelperState(enum.Enum):
	none = enum.auto()       # pre-waiting
	waiting = enum.auto()    # waiting
	confirmed = enum.auto()  # post-waiting
	aborted = enum.auto()    # post-waiting
	cancelled = enum.auto()  # post-waiting (abort silently)


class ConfirmHelper:
	def __init__(self):
		self.__lock = threading.Lock()
		self.__event = threading.Event()
		self.__state = ConfirmHelperState.none
		self.__is_waiting = False

	def wait(self, timeout: float) -> bool:
		with self.__lock:
			self.__state = ConfirmHelperState.waiting
			self.__is_waiting = True
		try:
			return self.__event.wait(timeout=timeout)
		finally:
			self.__is_waiting = False

	def is_waiting(self) -> bool:
		return self.__is_waiting

	def set(self, state: ConfirmHelperState):
		with self.__lock:
			if self.__state == ConfirmHelperState.waiting:
				self.__state = state
				self.__event.set()

	def get(self) -> ConfirmHelperState:
		with self.__lock:
			return self.__state

	def clear(self):
		with self.__lock:
			self.__event.clear()
			self.__state = ConfirmHelperState.none
