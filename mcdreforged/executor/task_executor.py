import time
from queue import Empty, PriorityQueue
from threading import Lock
from typing import Callable, Any, Optional

from mcdreforged import constant
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.mcdr_state import MCDReforgedState


class Priority:
	# High priority
	REGULAR = 0
	INFO = 20
	# Low priority


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
		self.task_queue = PriorityQueue(maxsize=constant.MAX_TASK_QUEUE_SIZE)
		self.__last_tick_time = None
		self.__stopped = False
		if previous_executor is not None:
			self.extract_tasks(previous_executor)

	def extract_tasks(self, other: 'TaskExecutor'):
		while True:
			try:
				task = other.task_queue.get(block=False)
			except Empty:
				break
			else:
				other.task_queue.task_done()  # marked the extract task as done
				self.task_queue.put(task)

	def should_keep_looping(self):
		return super().should_keep_looping() and not self.mcdr_server.is_mcdr_exit() and not self.mcdr_server.mcdr_in_state(MCDReforgedState.PRE_STOPPED)

	def soft_stop(self):
		"""
		Soft stop
		:return:
		"""
		self.__stopped = True

	def add_info_task(self, func: Callable[[], Any], is_user: bool):
		data = TaskData(func, Priority.INFO)
		if is_user:
			self.task_queue.put(data)
		else:
			self.task_queue.put_nowait(data)

	def add_task(self, func: Callable[[], Any]):
		self.task_queue.put(TaskData(func, Priority.REGULAR))

	def execute_or_enqueue(self, func: Callable[[], Any]):
		if self.is_on_thread():
			func()
		else:
			self.add_task(func)

	def get_this_tick_time(self) -> float:
		"""
		Return the duration of this tick
		If it's too long, something might go wrong
		"""
		if self.__last_tick_time is None:  # not started yet
			return 0
		return time.time() - self.__last_tick_time

	def tick(self):
		self.__last_tick_time = time.time()
		try:
			task = self.task_queue.get(timeout=0.01)
		except Empty:
			if self.__stopped:
				self.stop()
			return
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
