import threading
from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Optional, TYPE_CHECKING, TypeVar

from typing_extensions import override

from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.utils.exception import SelfJoinError

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin


_T = TypeVar('_T')


class TaskDoneFuture(Future):
	def __init__(self, runner_thread: threading.Thread):
		super().__init__()
		if not isinstance(runner_thread, threading.Thread):
			raise TypeError(type(runner_thread))
		self.__runner_thread = runner_thread

	def __self_join_check(self):
		if not self.done() and threading.current_thread() == self.__runner_thread:
			raise SelfJoinError('Cannot perform wait() on {} whose runner thread is current thread {}'.format(
				self.__class__.__name__, self.__runner_thread,
			))

	@override
	def result(self, timeout: Optional[float] = None) -> _T:
		self.__self_join_check()
		return super().result(timeout=timeout)

	@override
	def exception(self, timeout: Optional[float] = None) -> Optional[BaseException]:
		self.__self_join_check()
		return super().exception(timeout=timeout)


class TaskExecutorBase(BackgroundThreadExecutor, ABC):
	@abstractmethod
	def get_running_plugin(self) -> Optional['AbstractPlugin']:
		raise NotImplementedError()
