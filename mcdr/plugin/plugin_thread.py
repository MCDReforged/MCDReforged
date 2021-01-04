"""
Thread for plugin call
"""
import collections
import queue
import threading
from typing import Tuple, Any

from mcdr.plugin.plugin_event import EventListener

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
		self.original_name = 'PT{}-idle'.format(self.id)
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
					plugin = task_data.plugin
					plugin.plugin_manager.set_current_plugin(plugin)
					self.setName('PT{}@{}'.format(self.id, plugin.get_meta_data().id))
					self.thread_pool.working_count += 1
					try:
						task_data.callback()
					except:
						self.thread_pool.mcdr_server.logger.exception('Error invoking listener in plugin {}'.format(plugin))
					finally:
						self.thread_pool.working_count -= 1
						plugin.plugin_manager.set_current_plugin(None)
						self.setName(self.original_name)
				finally:
					if self.flag_interrupt:
						break
		finally:
			with self.thread_pool.threads_write_lock:
				self.thread_pool.threads.remove(self)

	def join(self, timeout=None):
		self.flag_interrupt = True
		super().join(timeout)


class PluginThreadPool:
	def __init__(self, mcdr_server, max_thread):
		self.mcdr_server = mcdr_server
		self.threads = []
		self.threads_write_lock = threading.Lock()
		self.task_queue = queue.Queue()
		self.working_count = 0
		self.max_thread = max_thread
		for i in range(self.max_thread):
			thread = PluginThread(self)
			thread.start()
			self.threads.append(thread)

	def set_max_thread(self, max_thread):
		self.max_thread = max_thread
		for i, thread in enumerate(self.threads.copy()):
			if i >= self.max_thread:
				thread.flag_interrupt = True

	def add_listener_execution_task(self, listener: EventListener, args: Tuple[Any, ...], forced_new_thread):
		"""
		Added a task to executing the callback of a listener to the dynamic thread pool and execute it
		If the thread pool is not enough a new temporary thread will start to process the task
		If forced_new_thread is set to true, the task will must be executed in a new temporary thread and will return
		the thread instance

		:param listener: The event listener to execute it's callback
		:param args: The arguments for the callback
		:param bool forced_new_thread: if set to true, it will force start a new thread for processing the task
		:return: None if forced_new_thread is False; The thread instance that is executing the task otherwise
		:rtype: PluginThread or None
		"""
		task_data = TaskData(callback=lambda: listener.execute(*args), plugin=listener.plugin)
		if forced_new_thread or self.working_count >= self.max_thread:
			thread = PluginThread(self, temporary=True, task=task_data)
			with self.threads_write_lock:
				self.threads.append(thread)
			thread.start()
			return thread if forced_new_thread else None
		else:
			self.task_queue.put(task_data)

	def join(self, timeout=None):
		for thread in self.threads.copy():
			thread.join(timeout)
