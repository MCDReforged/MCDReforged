import collections
import queue
import time
from typing import Callable, Any, Optional, Deque, NamedTuple

from mcdreforged.constants import core_constant
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.utils.future import WaitableCallable
from mcdreforged.utils.logger import DebugOption


class TaskData(NamedTuple):
	func: Callable
	vip: bool


class DoubleQueue(queue.Queue[TaskData]):
	def __init__(self, maxsize: int):
		super().__init__(maxsize)
		self.__queue0: Deque[TaskData]  # VIP
		self.__queue1: Deque[TaskData]  # Regular

	def _init(self, maxsize: int) -> None:
		self.__queue0 = collections.deque()
		self.__queue1 = collections.deque()

	def _qsize(self) -> int:
		return len(self.__queue0) + len(self.__queue1)

	def _put(self, item: TaskData):
		if item.vip:
			self.__queue0.append(item)
		else:
			self.__queue1.append(item)

	def _get(self) -> TaskData:
		if len(self.__queue0) > 0:
			return self.__queue0.popleft()
		return self.__queue1.popleft()


class TaskExecutor(ThreadExecutor):
	def __init__(self, mcdr_server, *, previous_executor: 'Optional[TaskExecutor]' = None):
		super().__init__(mcdr_server)
		self.task_queue = DoubleQueue(maxsize=core_constant.MAX_TASK_QUEUE_SIZE)
		self.__last_tick_time = None
		self.__soft_stopped = False
		if previous_executor is not None:
			self.extract_tasks(previous_executor)

	def extract_tasks(self, other: 'TaskExecutor'):
		count = 0
		while True:
			try:
				task = other.task_queue.get(block=False)
			except queue.Empty:
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
		data = TaskData(func, False)
		if is_user:
			self.task_queue.put(data)
		else:
			self.task_queue.put_nowait(data)

	def add_regular_task(self, func: Callable[[], Any], *, block: bool = False, timeout: Optional[float] = None):
		if block:
			func = WaitableCallable(func)
		self.task_queue.put(TaskData(func, True))
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
		except queue.Empty:
			if self.__soft_stopped:
				self.stop()
		else:
			try:
				task.func()
			except Exception:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('task_executor.error'))
			finally:
				self.task_queue.task_done()

	def wait_till_finish_all_task(self):
		if self.is_on_thread():
			raise RuntimeError('Cannot wait in self\'s thread')
		self.task_queue.join()
