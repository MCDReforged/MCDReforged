import asyncio
import threading
from typing import TYPE_CHECKING, Optional, Coroutine, Any, Callable

from typing_extensions import override

from mcdreforged.executor.task_executor_common import TaskDoneEvent, TaskExecutorBase

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class AsyncTaskExecutor(TaskExecutorBase):
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.__start_ok_event = threading.Event()
		self.__stop_flag = False

		self.__event_loop: Optional[asyncio.AbstractEventLoop] = None
		self.__stop_event: Optional[asyncio.Event] = None
		self.__submitted_tasks: Optional[asyncio.Queue[asyncio.Task]] = None

	def get_event_loop(self) -> asyncio.AbstractEventLoop:
		return self.__event_loop

	@override
	def get_running_plugin(self) -> Optional['AbstractPlugin']:
		task = asyncio.current_task(self.__event_loop)
		return getattr(task, '_mcdr_running_plugin', None)

	def submit(self, coro: Coroutine, *, plugin: Optional['AbstractPlugin'] = None) -> threading.Event:
		done_event = TaskDoneEvent(self.get_thread())
		if self.__stop_flag:
			self.logger.warning('Submitting async coroutine to a stopped AsyncTaskExecutor, dropped')
			done_event.set()
		else:
			def create_task():
				task = self.__event_loop.create_task(coro)
				task.add_done_callback(lambda t: done_event.set())
				setattr(task, '_mcdr_running_plugin', plugin)
				self.__submitted_tasks.put_nowait(task)
			self.call_soon_threadsafe(create_task)
		return done_event

	def call_soon_threadsafe(self, func: Callable[[], Any]):
		self.__event_loop.call_soon_threadsafe(func)

	@override
	def start(self):
		super().start()
		self.__start_ok_event.wait()

	@override
	def stop(self):
		if self.__stop_flag:
			raise RuntimeError('double stop')

		self.__stop_flag = True
		self.__event_loop.call_soon_threadsafe(self.__stop_event.set)

	@override
	def loop(self):
		asyncio.run(self.__async_loop())

	@override
	def tick(self):
		raise RuntimeError('not implemented')

	async def __async_loop(self):
		self.__event_loop = asyncio.get_event_loop()
		self.__stop_event = asyncio.Event()
		self.__submitted_tasks = asyncio.Queue()
		self.__start_ok_event.set()
		
		stop_sentinel = object()

		# ensure all running tasks are done
		async def task_awaiter():
			while True:
				task_coro = await self.__submitted_tasks.get()
				if task_coro is stop_sentinel:
					break

				try:
					await task_coro
				except Exception:
					self.logger.exception('queue_drainer await error')

		task_ta = asyncio.create_task(task_awaiter())
		await self.__stop_event.wait()

		self.__submitted_tasks.put_nowait(stop_sentinel)
		await task_ta
