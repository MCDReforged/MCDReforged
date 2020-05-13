# -*- coding: utf-8 -*-
import collections
import queue
import threading


TaskData = collections.namedtuple('TaskData', 'func args func_name plugin')


class PluginThread(threading.Thread):
	counter = 0

	def __init__(self, thread_pool, temporary=False):
		super().__init__()
		self.daemon = True
		self.thread_pool = thread_pool
		self.flag_interrupt = temporary
		self.plugin = None
		self.id = PluginThread.counter
		PluginThread.counter += 1
		self.original_name = '{}-{}'.format(type(self).__name__, self.id)
		self.setName(self.original_name)

	def run(self):
		try:
			while True:
				try:
					task_data = self.thread_pool.task_queue.get(timeout=0.01)
				except queue.Empty:
					pass
				else:
					self.plugin = task_data.plugin
					self.setName('PT{}-{}@{}'.format(self.id, task_data.func_name, self.plugin.plugin_name))
					self.thread_pool.working_count += 1
					try:
						task_data.func(*task_data.args)
					except:
						self.thread_pool.server.logger.exception('Error calling {} in plugin {}'.format(task_data.func_name, self.plugin.plugin_name))
					finally:
						self.thread_pool.working_count -= 1
						self.plugin = None
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
	def __init__(self, server, max_thread=4):
		self.server = server
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
		for i, thread in enumerate(self.threads[:]):
			if i >= self.max_thread:
				thread.flag_interrupt = True

	def add_task(self, func, args, func_name, plugin):
		task_data = TaskData(func, args, func_name, plugin)
		self.task_queue.put(task_data)
		if self.working_count >= self.max_thread:
			thread = PluginThread(self, temporary=True)
			with self.threads_write_lock:
				self.threads.append(thread)
			thread.start()

	def join(self, timeout=None):
		for thread in self.threads[:]:
			thread.join(timeout)
