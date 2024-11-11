import threading
import traceback
from abc import abstractmethod
from typing import Optional, TYPE_CHECKING

from mcdreforged.utils import misc_utils

if TYPE_CHECKING:
	from mcdreforged.logging.logger import MCDReforgedLogger


def _get_thread_stack(thread: threading.Thread) -> Optional[traceback.StackSummary]:
	# noinspection PyProtectedMember
	from sys import _current_frames
	if (frame := _current_frames().get(thread.ident)) is None:
		return None
	return traceback.extract_stack(frame)


class BackgroundThreadExecutor:
	def __init__(self, logger: 'MCDReforgedLogger'):
		self.logger = logger
		self._executor_thread: Optional[threading.Thread] = None
		self.__stopped_looping = False
		self.__name = self.__class__.__name__

	def get_thread(self) -> Optional[threading.Thread]:
		return self._executor_thread

	def get_thread_stack(self) -> Optional[traceback.StackSummary]:
		if (thread := self._executor_thread) is None:
			return None
		return _get_thread_stack(thread)

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
		if (thread := self._executor_thread) is not None:
			thread.name = name

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
