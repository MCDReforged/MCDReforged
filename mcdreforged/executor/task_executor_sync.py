import collections
import contextlib
from concurrent.futures import Future
from typing import Callable, Optional, TYPE_CHECKING, Dict, TypeVar

from typing_extensions import override, Deque

from mcdreforged.executor.task_executor_common import TaskExecutorBase, TaskDoneFuture
from mcdreforged.executor.task_executor_queue import TaskQueue, TaskPriority, TaskQueueItem
from mcdreforged.logging.debug_option import DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin


_T = TypeVar('_T')


class SyncTaskExecutor(TaskExecutorBase):
	__soft_stop_sentinel = TaskQueueItem(lambda: None, TaskPriority.SENTINEL, None, Future())

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.mcdr_server = mcdr_server
		self.__task_queue = TaskQueue()
		self.__running_plugins: Deque['AbstractPlugin'] = collections.deque()
		self.set_name('TaskExecutor')

	def extract_tasks_from(self, other: 'SyncTaskExecutor'):
		tasks = other.__task_queue.drain_all_tasks()
		for task in tasks:
			self.__task_queue.put(task)
		self.mcdr_server.logger.mdebug('Extracted {} tasks from the previous executor'.format(len(tasks)), option=DebugOption.TASK_EXECUTOR)

	def get_queue_sizes(self) -> Dict[TaskPriority, int]:
		return self.__task_queue.queue_sizes()

	def submit(
			self, func: Callable[[], _T], *,
			priority: TaskPriority = TaskPriority.REGULAR,
			raise_if_full: bool = False,
			need_future: bool = True,
			plugin: Optional['AbstractPlugin'] = None,
	) -> Optional[Future[_T]]:
		if not self._executor_thread.is_alive():
			self.logger.error('Submitting task to a dead task executor {}, thread {}'.format(self, self._executor_thread.ident))
		if need_future:
			future = TaskDoneFuture(self.get_thread())
		else:
			future = None
		item = TaskQueueItem(func, priority, plugin=plugin, future=future)
		self.__task_queue.put(item, block=not raise_if_full)
		return future

	@override
	def should_keep_looping(self) -> bool:
		return super().should_keep_looping() and not self.mcdr_server.is_mcdr_exit()

	@override
	def get_running_plugin(self) -> Optional['AbstractPlugin']:
		try:
			return self.__running_plugins[-1]
		except IndexError:
			return None

	def soft_stop(self):
		self.__task_queue.put(self.__soft_stop_sentinel)

	@contextlib.contextmanager
	def __with_plugin(self, plugin: 'AbstractPlugin'):
		if not self.is_on_thread():
			raise AssertionError()
		self.__running_plugins.append(plugin)
		try:
			yield
		finally:
			self.__running_plugins.pop()

	@override
	def tick(self):
		task = self.__task_queue.get()
		if task is self.__soft_stop_sentinel:
			self.stop()
			return

		with self.__with_plugin(task.plugin):
			try:
				task_result = task.func()
			except Exception as e:
				self.mcdr_server.logger.exception(self.mcdr_server.translate('mcdreforged.task_executor.error'))
				if task.future is not None:
					task.future.set_exception(e)
			else:
				if task.future is not None:
					task.future.set_result(task_result)

	@contextlib.contextmanager
	def with_plugin_if_on_thread(self, plugin: 'AbstractPlugin'):
		if self.is_on_thread():
			with self.__with_plugin(plugin):
				yield
		else:
			yield
