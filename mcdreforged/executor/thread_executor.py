import threading
from typing import TYPE_CHECKING

from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class ThreadExecutor:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.executor_thread = None

	def is_on_thread(self):
		return threading.current_thread() is self.executor_thread

	def should_keep_looping(self):
		raise NotImplementedError()

	def start(self):
		self.mcdr_server.logger.debug('{} is starting'.format(self.get_name()))
		self.executor_thread = misc_util.start_thread(self.loop, (), self.get_name())
		return self.executor_thread

	def get_name(self):
		return self.__class__.__name__

	def loop(self):
		while self.should_keep_looping():
			self.tick()

	def tick(self):
		raise NotImplementedError()

	def join(self):
		if self.executor_thread is None:
			raise RuntimeError()
		self.executor_thread.join()
