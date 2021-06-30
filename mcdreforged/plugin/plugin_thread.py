"""
Thread for plugin call
"""
import collections
import queue
import threading
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin


TaskData = collections.namedtuple('TaskData', 'callback plugin')


class PluginThread(threading.Thread):
	counter = 0

	def __init__(self, thread_pool, temporary=False, task=None):
		super().__init__()
		self.daemon = True
		self.thread_pool = thread_pool
		self.flag_interrupt = temporary
		self.task = task
		self.id = PluginThread.counter
		PluginThread.counter += 1
		self.original_name = '{}-idle'.format(self)
		self.setName(self.original_name)

	def run(self):
		try:
			while True:
				try:
					if self.task is not None:
						task_data = self.task
						self.task = None
					else:
						task_data = self.thread_pool.task_queue.get(timeout=0.01)  # type: TaskData
				except queue.Empty:
					pass
				else:
					plugin = task_data.plugin  # type: AbstractPlugin
					with plugin.plugin_manager.with_plugin_context(plugin):
						self.setName('{}@{}'.format(self, plugin.get_id()))
						self.thread_pool.working_count += 1
						try:
							task_data.callback()
						except:
							self.thread_pool.mcdr_server.logger.exception('Exception in thread created by {}'.format(plugin))
						finally:
							self.thread_pool.working_count -= 1
							self.setName(self.original_name)
				finally:
					if self.flag_interrupt:
						break
		finally:
			with self.thread_pool.threads_write_lock:
				self.thread_pool.threads.remove(self)

	def set_interrupt(self):
		self.flag_interrupt = True

	def join(self, timeout=None):
		self.set_interrupt()
		super().join(timeout)

	def __repr__(self):
		return '{}{}'.format(self.__class__.__name__, self.id)


class PluginThreadPool:
	def __init__(self, mcdr_server: 'MCDReforgedServer', max_thread):
		self.mcdr_server = mcdr_server
		self.threads = []
		self.threads_write_lock = threading.Lock()
		self.task_queue = queue.Queue()
		self.working_count = 0
		self.max_thread = max_thread

	def start(self):
		for i in range(self.max_thread):
			thread = PluginThread(self)
			thread.start()
			self.threads.append(thread)

	def set_max_thread(self, max_thread):
		self.max_thread = max_thread
		for i, thread in enumerate(self.threads.copy()):
			if i >= self.max_thread:
				thread.set_interrupt()

	def add_task(self, func: Callable, plugin: 'AbstractPlugin'):
		"""
		Added a task to executing the callback of a listener to the dynamic thread pool and execute it
		If the thread pool is not enough a new temporary thread will start to process the task
		"""
		task_data = TaskData(callback=func, plugin=plugin)
		if self.working_count >= self.max_thread:
			thread = PluginThread(self, temporary=True, task=task_data)
			with self.threads_write_lock:
				self.threads.append(thread)
			thread.start()
			return thread
		else:
			self.task_queue.put(task_data)

	def join(self, timeout=None):
		for thread in self.threads.copy():
			thread.join(timeout)
