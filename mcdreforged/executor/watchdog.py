import time

from mcdreforged.executor.task_executor import TaskExecutor
from mcdreforged.executor.thread_executor import ThreadExecutor


class WatchDog(ThreadExecutor):
	TASK_EXECUTOR_NO_RESPOND_THRESHOLD = 10  # seconds

	def check_task_executor_state(self):
		task_executor = self.mcdr_server.task_executor
		if task_executor.get_this_tick_time() > self.TASK_EXECUTOR_NO_RESPOND_THRESHOLD:
			plugin = self.mcdr_server.plugin_manager.get_current_running_plugin(thread=task_executor.get_thread())
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line1', self.TASK_EXECUTOR_NO_RESPOND_THRESHOLD))
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line2', plugin))
			self.mcdr_server.logger.warning(self.mcdr_server.tr('watchdog.task_executor_no_response.line3'))

			task_executor.soft_stop()  # Soft-stop it, in case it turns alive somehow
			task_executor.set_name(task_executor.get_name() + ' (no response)')

			new_executor = TaskExecutor(self.mcdr_server, previous_executor=task_executor)
			self.mcdr_server.task_executor = new_executor
			new_executor.start()

	def tick(self):
		try:
			time.sleep(0.1)
			self.check_task_executor_state()
		except:
			self.mcdr_server.logger.exception('Error ticking watch dog')
