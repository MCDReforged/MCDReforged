import threading
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING

from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class SelfJoinError(Exception):
	pass


class TaskDoneEvent(threading.Event):
	def __init__(self, runner_thread: threading.Thread):
		super().__init__()
		if not isinstance(runner_thread, threading.Thread):
			raise TypeError(type(runner_thread))
		self.__runner_thread = runner_thread

	def wait(self, timeout: Optional[float] = None) -> bool:
		if not self.is_set() and threading.current_thread() == self.__runner_thread:
			raise SelfJoinError('Cannot perform wait() on TaskDoneEvent whose runner thread is current thread {}'.format(self.__runner_thread))
		return super().wait(timeout=timeout)


class TaskExecutorBase(BackgroundThreadExecutor, ABC):
	@abstractmethod
	def get_running_plugin(self) -> Optional['AbstractPlugin']:
		raise NotImplementedError()
