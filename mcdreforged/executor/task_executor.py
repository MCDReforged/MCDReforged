import time
from queue import Empty, PriorityQueue
from threading import Lock
from typing import Callable, Any, Optional

from mcdreforged.constants import core_constant
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import DebugOption


class Priority:
	# High priority, executes first
	REGULAR = 0
	INFO = 20
	# Low priority, executes last


class TaskData:
	ID_COUNTER = 0
	ID_COUNTER_LOCK = Lock()

	def __init__(self, func: Callable, priority: int):
		if not isinstance(func, Callable):
			raise TypeError('func should be a callable object')
		self.func = func
		self.priority = priority
		with TaskData.ID_COUNTER_LOCK:
			self.id = TaskData.ID_COUNTER
			TaskData.ID_COUNTER += 1

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		if self.priority != other.priority:
			return self.priority < other.priority
		else:
			return self.id < other.id


class TaskExecutor(ThreadExecutor):
	def __init__(self, mcdr_server, *, previous_executor: 'Optional[TaskExecutor]' = None):
		super().__init__(mcdr_server)
		self.task_queue = PriorityQueue(maxsize=core_constant.MAX_TASK_QUEUE_SIZE)
		self.__last_tick_time = None
		self.__soft_stopped = False
		if previous_executor is not None:
			self.extract_tasks(previous_executor)

	def extract_tasks(self, other: 'TaskExecutor'):
		count = 0
		while True:
			try:
				task = other.task_queue.get(block=False)
			except Empty:
				break
			else:
				count += 1
				other.task_queue.task_done()  # marked the extracted task as done
				self.task_queue.put(task)
		self.mcdr_server.logger.debug('Extracted {} tasks from the previous executor'.format(count), option=DebugOption.TASK_EXECUTOR)

	def should_keep_looping(self):
		return super().should_keep_looping() and not self.mcdr_server.is_mcdr_exit()

	def soft_stop(self):
		self.__soft_stopped = True

	def enqueue_info_task(self, func: Callable[[], Any], is_user: bool):
		data = TaskData(func, Priority.INFO)
		if is_user:
			self.task_queue.put(data)
		else:
			self.task_queue.put_nowait(data)

	def add_regular_task(self, func: Callable[[], Any], *, block: bool = False, timeout: Optional[float] = None):
		if block:
			func = misc_util.WaitableCallable(func)
		self.task_queue.put(TaskData(func, Priority.REGULAR))
		if block:
			func.wait(timeout)

	def execute_on_thread(self, func: Callable[[], Any], *, block: bool = False, timeout: Optional[float] = None):
		if self.is_on_thread():
			func()
		else:
			self.add_regular_task(func, block=block, timeout=timeout)

	def get_this_tick_time(self) -> float:
		"""
		Return the duration of this tick
		If it's too long, something might go wrong
		"""
		if self.__last_tick_time is None:  # not started yet
			return 0
		return time.monotonic() - self.__last_tick_time

	def tick(self):
		self.__last_tick_time = time.monotonic()
		try:
			task = self.task_queue.get(timeout=0.01)
		except Empty:
			if self.__soft_stopped:
				self.stop()
		else:
			try:
				task.func()
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('task_executor.error'))
			finally:
				self.task_queue.task_done()

	def wait_till_finish_all_task(self):
		if self.is_on_thread():
			raise RuntimeError('Cannot wait in self\'s thread')
		self.task_queue.join()
