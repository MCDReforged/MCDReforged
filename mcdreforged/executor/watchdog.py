import time
from contextlib import contextmanager
from typing import TYPE_CHECKING

from mcdreforged.executor.task_executor import TaskExecutor
from mcdreforged.executor.thread_executor import ThreadExecutor

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class WatchDog(ThreadExecutor):
	DEFAULT_NO_RESPOND_THRESHOLD = 10  # seconds

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server)
		self.__monitoring = False

	def is_monitoring(self):
		return self.__monitoring

	def pause(self):
		self.__monitoring = False

	def resume(self):
		self.__monitoring = True

	@contextmanager
	def pausing(self):
		self.pause()
		try:
			yield
		finally:
			self.resume()

	def check_task_executor_state(self):
		task_executor = self.mcdr_server.task_executor
		no_respond_threshold = self.mcdr_server.config['watchdog_threshold']  # in seconds
		if not isinstance(no_respond_threshold, (int, float)):
			no_respond_threshold = self.DEFAULT_NO_RESPOND_THRESHOLD
		if no_respond_threshold <= 0:
			return
		if task_executor.get_this_tick_time() > no_respond_threshold and self.__monitoring:
			plugin = self.mcdr_server.plugin_manager.get_current_running_plugin(thread=task_executor.get_thread())
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line1', no_respond_threshold))
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line2', plugin))
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line3'))

			task_executor.soft_stop()  # Soft-stop it, in case it turns alive somehow
			task_executor.set_name(task_executor.get_name() + ' (no response)')

			new_executor = TaskExecutor(self.mcdr_server, previous_executor=task_executor)
			self.mcdr_server.set_task_executor(new_executor)
			new_executor.start()

	def start(self):
		super().start()
		self.__monitoring = True

	def tick(self):
		try:
			time.sleep(0.1)
			self.check_task_executor_state()
		except:
			self.mcdr_server.logger.exception('Error ticking watch dog')
