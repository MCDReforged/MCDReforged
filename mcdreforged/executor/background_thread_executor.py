import threading
from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

from mcdreforged.utils import misc_utils

if TYPE_CHECKING:
	from mcdreforged.utils.logger import MCDReforgedLogger


class BackgroundThreadExecutor:
	def __init__(self, logger: 'MCDReforgedLogger'):
		self.logger = logger
		self._executor_thread: Optional[threading.Thread] = None
		self.__stopped_looping = False
		self.__name = self.__class__.__name__

	def get_thread(self) -> Optional[threading.Thread]:
		return self._executor_thread

	def is_on_thread(self):
		return threading.current_thread() is self._executor_thread

	def should_keep_looping(self) -> bool:
		return not self.__stopped_looping

	def start(self):
		self.logger.debug('BackgroundThreadExecutor {} is starting'.format(self.get_name()))
		self._executor_thread = misc_utils.start_thread(self.loop, (), self.get_name())
		return self._executor_thread

	def stop(self):
		self.__stopped_looping = True

	def get_name(self) -> str:
		return self.__name

	def set_name(self, name: str):
		self.__name = name
		self._executor_thread.setName(name)

	def loop(self):
		while self.should_keep_looping():
			self.tick()

	@abstractmethod
	def tick(self):
		raise NotImplementedError()

	def join(self):
		if self._executor_thread is None:
			raise RuntimeError()
		self._executor_thread.join()
