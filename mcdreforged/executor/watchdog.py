import time

from mcdreforged.executor.task_executor import TaskExecutor
from mcdreforged.executor.thread_executor import ThreadExecutor


class WatchDog(ThreadExecutor):
	TASK_EXECUTOR_NO_RESPOND_THRESHOLD = 60  # 60 seconds

	def check_task_executor_state(self):
		task_executor = self.mcdr_server.task_executor
		logger = self.mcdr_server.logger
		if task_executor.get_this_tick_time() > self.TASK_EXECUTOR_NO_RESPOND_THRESHOLD:
			logger.warning('Task executor has no respond for {} seconds, something might go wrong'.format(self.TASK_EXECUTOR_NO_RESPOND_THRESHOLD))
			logger.warning('Current running plugin (if there\'s any): {}'.format(self.mcdr_server.plugin_manager.get_current_running_plugin(thread=task_executor.get_thread())))
			logger.warning('Recreating the task executor')
			task_executor.soft_stop()  # Soft-stop it, in case it turns alive somehow
			task_executor.set_name(task_executor.get_name() + ' (no response)')

			task_executor = TaskExecutor(self.mcdr_server)
			task_executor.start()
			self.mcdr_server.task_executor = task_executor

	def tick(self):
		try:
			time.sleep(0.1)
			self.check_task_executor_state()
		except:
			self.mcdr_server.logger.exception('Error ticking watch dog')
