import queue
import threading
from typing import Callable, Any, Optional, TYPE_CHECKING, Dict

from typing_extensions import override

from mcdreforged.executor.task_executor_common import TaskDoneEvent, TaskExecutorBase
from mcdreforged.executor.task_executor_queue import TaskQueue, TaskPriority, TaskQueueItem
from mcdreforged.logging.debug_option import DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class SyncTaskExecutor(TaskExecutorBase):
	__soft_stop_sentinel = TaskQueueItem(lambda: None, TaskPriority.SENTINEL)

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.mcdr_server = mcdr_server
		self.__task_queue = TaskQueue()
		self.__running_plugin: Optional['AbstractPlugin'] = None
		self.set_name('TaskExecutor')

	def drain_tasks_from(self, other: 'SyncTaskExecutor'):
		count = 0
		while True:
			try:
				task = other.__task_queue.get(block=False)
			except queue.Empty:
				break
			else:
				count += 1
				self.__task_queue.put(task)
		self.mcdr_server.logger.mdebug('Extracted {} tasks from the previous executor'.format(count), option=DebugOption.TASK_EXECUTOR)

	def get_queue_sizes(self) -> Dict[TaskPriority, int]:
		return self.__task_queue.qsizes()

	def submit(self, func: Callable[[], Any], *, priority: TaskPriority = TaskPriority.REGULAR, raise_if_full: bool = False, plugin: Optional['AbstractPlugin'] = None) -> threading.Event:
		done_event = TaskDoneEvent(self.get_thread())
		item = TaskQueueItem(func, priority, plugin=plugin, done_event=done_event)
		self.__task_queue.put(item, block=not raise_if_full)
		return done_event

	@override
	def should_keep_looping(self) -> bool:
		return super().should_keep_looping() and not self.mcdr_server.is_mcdr_exit()

	@override
	def get_running_plugin(self) -> Optional['AbstractPlugin']:
		return self.__running_plugin

	def soft_stop(self):
		self.__task_queue.put(self.__soft_stop_sentinel)

	@override
	def tick(self):
		task = self.__task_queue.get()
		if task is self.__soft_stop_sentinel:
			self.stop()
			return

		self.__running_plugin = task.plugin
		try:
			task.func()
		except Exception:
			self.mcdr_server.logger.exception(self.mcdr_server.translate('mcdreforged.task_executor.error'))
		finally:
			self.__running_plugin = None
			if (done_event := task.done_event) is not None:
				done_event.set()
