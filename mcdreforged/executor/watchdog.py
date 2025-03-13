import time
from concurrent.futures import Future
from contextlib import contextmanager
from typing import TYPE_CHECKING

from typing_extensions import override

from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.executor.task_executor_common import TaskExecutorBase
from mcdreforged.executor.task_executor_queue import TaskPriority
from mcdreforged.executor.task_executor_sync import SyncTaskExecutor
from mcdreforged.utils import future_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class WatchDog(BackgroundThreadExecutor):
	DEFAULT_NO_RESPOND_THRESHOLD = 10  # seconds

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.mcdr_server = mcdr_server
		self.__tr = mcdr_server.create_internal_translator('watchdog').tr
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

	def __wait_future(self, future: Future, timeout: float) -> bool:
		n = 5
		for _ in range(n):
			if not self.__monitoring or future_utils.wait(future, timeout / n) or not self.__monitoring:
				return True
		return False

	def __show_executor(self, executor: TaskExecutorBase, no_respond_threshold: float, can_rebuild: bool):
		plugin = executor.get_running_plugin()
		thread_name = executor.get_thread().name
		self.mcdr_server.logger.warning(self.__tr('task_executor_no_response.line1', thread_name, no_respond_threshold))
		self.mcdr_server.logger.warning(self.__tr('task_executor_no_response.line2', thread_name, plugin))

		if (ss := executor.get_thread_stack()) is not None:
			for line in ss.get_lines():
				self.mcdr_server.logger.warning(line)

		if can_rebuild:
			self.mcdr_server.logger.warning(self.__tr('task_executor_no_response.line3', thread_name))

	def __check_sync_task_executor(self, no_respond_threshold: float):
		executor = self.mcdr_server.task_executor
		future = executor.submit(lambda: None, priority=TaskPriority.HIGH)
		if self.__wait_future(future, no_respond_threshold):
			return

		self.__show_executor(executor, no_respond_threshold, True)

		executor.soft_stop()  # Soft-stop it, in case it turns alive somehow
		executor.set_name(executor.get_name() + ' (no response)')

		new_executor = SyncTaskExecutor(self.mcdr_server)
		new_executor.extract_tasks_from(executor)
		new_executor.start()
		self.mcdr_server.set_task_executor(new_executor)

	def __check_async_task_executor(self, no_respond_threshold: float):
		executor = self.mcdr_server.async_task_executor
		future = Future()
		executor.call_soon_threadsafe(future.cancel)

		if self.__wait_future(future, no_respond_threshold):
			return

		self.__show_executor(executor, no_respond_threshold, False)

	def __check_stuffs(self):
		no_respond_threshold = self.mcdr_server.config.watchdog_threshold  # in seconds
		if not isinstance(no_respond_threshold, (int, float)):
			no_respond_threshold = self.DEFAULT_NO_RESPOND_THRESHOLD

		if no_respond_threshold <= 0:
			return
		if not self.__monitoring:
			return

		self.__check_sync_task_executor(no_respond_threshold)
		self.__check_async_task_executor(no_respond_threshold)

	@override
	def start(self):
		super().start()
		self.__monitoring = True

	@override
	def tick(self):
		try:
			time.sleep(0.1)
			self.__check_stuffs()
		except Exception:
			self.mcdr_server.logger.exception('Error ticking watch dog')
