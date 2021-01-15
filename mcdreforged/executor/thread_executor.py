import threading
from typing import TYPE_CHECKING, Optional

from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class ThreadExecutor:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self._executor_thread = None  # type: Optional[threading.Thread]
		self.__stopped_looping = False
		self.__name = self.__class__.__name__

	def get_thread(self) -> Optional[threading.Thread]:
		return self._executor_thread

	def is_on_thread(self):
		return threading.current_thread() is self._executor_thread

	def should_keep_looping(self) -> bool:
		return not self.__stopped_looping

	def start(self):
		self.mcdr_server.logger.debug('{} is starting'.format(self.get_name()))
		self._executor_thread = misc_util.start_thread(self.loop, (), self.get_name())
		return self._executor_thread

	def stop(self):
		self.__stopped_looping = True

	def get_name(self):
		return self.__name

	def set_name(self, name: str):
		self.__name = name
		self._executor_thread.setName(name)

	def loop(self):
		while self.should_keep_looping():
			self.tick()

	def tick(self):
		raise NotImplementedError()

	def join(self):
		if self._executor_thread is None:
			raise RuntimeError()
		self._executor_thread.join()
