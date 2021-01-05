from queue import Empty, PriorityQueue
from typing import Callable, Any

from mcdreforged import constant
from mcdreforged.executor.thread_executor import ThreadExecutor


class Priority:
	# High priority
	REGULAR = 0
	INFO = 20
	# Low priority


class TaskData:
	def __init__(self, func: Callable, priority: int):
		if not isinstance(func, Callable):
			raise TypeError('func should be a callable object')
		self.func = func
		self.priority = priority

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.priority < other.priority


class TaskExecutor(ThreadExecutor):
	def __init__(self, mcdr_server):
		super().__init__(mcdr_server)
		self.task_queue = PriorityQueue(maxsize=constant.MAX_TASK_QUEUE_SIZE)

	def should_keep_looping(self):
		return not self.mcdr_server.is_mcdr_exit()

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

	def tick(self):
		try:
			task = self.task_queue.get(timeout=0.01)
		except Empty:
			return
		try:
			task.func()
		except:
			self.mcdr_server.logger.exception('Error executing task')  # TODO: translation
		finally:
			self.task_queue.task_done()

	def wait_till_finish_all_task(self):
		if self.is_on_thread():
			raise RuntimeError('Cannot wait in self\'s thread')
		self.task_queue.join()
