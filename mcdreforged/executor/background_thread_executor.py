import threading
from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

from mcdreforged.utils import thread_utils

if TYPE_CHECKING:
	from mcdreforged.logging.logger import MCDReforgedLogger


class BackgroundThreadExecutor:
	def __init__(self, logger: 'MCDReforgedLogger'):
		self.logger = logger
		self.__executor_thread: Optional[threading.Thread] = None
		self.__stopped_looping = threading.Event()
		self.__name = self.__class__.__name__

	@property
	def _executor_thread(self) -> Optional[threading.Thread]:
		return self.__executor_thread

	@_executor_thread.setter
	def _executor_thread(self, thread: threading.Thread):
		if self.__executor_thread and thread != self.__executor_thread:
			raise RuntimeError('Assigning executor_thread to another thread, old {}, new {}'.format(self.__executor_thread, thread))
		self.__executor_thread = thread

	def get_thread(self) -> Optional[threading.Thread]:
		return self._executor_thread

	def get_thread_stack(self) -> Optional[thread_utils.ThreadStackInfo]:
		if (thread := self._executor_thread) is None:
			return None
		if not thread.is_alive():
			return None
		return thread_utils.get_stack_info(thread)

	def is_on_thread(self):
		return threading.current_thread() is self._executor_thread

	def should_keep_looping(self) -> bool:
		return not self.__stopped_looping.is_set()

	def start(self):
		if self._executor_thread is not None:
			raise RuntimeError('Already started')
		self.logger.debug('BackgroundThreadExecutor {} is starting'.format(self.get_name()))
		self._executor_thread = thread_utils.start_thread(self.__loop_entry, (), self.get_name())
		return self._executor_thread

	def stop(self):
		self.__stopped_looping.set()

	def _wait_for_stop(self, timeout: float):
		self.__stopped_looping.wait(timeout=timeout)

	def get_name(self) -> str:
		return self.__name

	def set_name(self, name: str):
		self.__name = name
		if (thread := self._executor_thread) is not None:
			thread.name = name

	def __loop_entry(self):
		self._executor_thread = threading.current_thread()
		self.loop()

	def loop(self):
		while self.should_keep_looping():
			self.tick()

	@abstractmethod
	def tick(self):
		raise NotImplementedError()

	def join(self, timeout: Optional[float] = None):
		if self._executor_thread is None:
			raise RuntimeError()
		self._executor_thread.join(timeout)
