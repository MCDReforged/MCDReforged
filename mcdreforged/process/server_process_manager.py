import asyncio
import concurrent.futures as cf
import contextlib
import dataclasses
import queue
import threading
import time
from pathlib import Path
from typing import Optional, Union, List, TYPE_CHECKING

import psutil

from mcdreforged.utils import collection_utils, thread_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class ProcessNotRunning(Exception):
	pass


class ProcessAlreadyRunning(Exception):
	pass


class ProcessStillAlive(Exception):
	pass


@dataclasses.dataclass(frozen=True)
class ServerOutput:
	line: bytes  # might have a '\n' suffix
	is_stdout: bool  # true: stdout, false: stderr


_SERVER_OUTPUT_EOF_SENTINEL = ServerOutput(b'', False)


@dataclasses.dataclass(frozen=True)
class _RunningProcess:
	proc: asyncio.subprocess.Process
	loop: asyncio.AbstractEventLoop
	thread: threading.Thread

	def is_proc_alive_and_loop_available(self) -> bool:
		return self.proc.returncode is None and not self.loop.is_closed() and self.thread.is_alive()


class ServerProcessManager:
	MAX_OUTPUT_QUEUE_SIZE = 1024

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.logger = mcdr_server.logger
		self.__tr = mcdr_server.create_internal_translator('process').tr
		self.__output_queue: 'queue.Queue[ServerOutput]' = queue.Queue(maxsize=self.MAX_OUTPUT_QUEUE_SIZE)
		self.__current_process: Optional[_RunningProcess] = None

	def __del__(self):
		if self.is_alive():
			with contextlib.suppress(Exception):
				self.kill_process_tree(quiet=True)

	def start(self, args: Union[str, List[str]], cwd: Path):
		if self.__current_process is not None:
			raise ProcessAlreadyRunning('server process already started')

		async def drain_reader(reader: asyncio.StreamReader, is_stdout: bool):
			queue_full_warn_ts = 0
			while line := await reader.readline():
				self.__output_queue.put(ServerOutput(line, is_stdout))
				if self.__output_queue.full():
					now = time.time()
					if now - queue_full_warn_ts >= 10:
						queue_full_warn_ts = now
						self.logger.warning('output queue is full')

		async def run_process():
			try:
				event_loop_future.set_result(asyncio.get_event_loop())
				common_kwargs = dict(
					cwd=cwd,
					stdin=asyncio.subprocess.PIPE,
					stdout=asyncio.subprocess.PIPE,
					stderr=asyncio.subprocess.PIPE,
				)
				if isinstance(args, str):
					proc = await asyncio.create_subprocess_shell(args, **common_kwargs)
				else:
					proc = await asyncio.create_subprocess_exec(*args, **common_kwargs)
			except Exception as e:
				proc_future.set_exception(e)
				raise
			else:
				proc_future.set_result(proc)

			async def set_output_eof():
				await asyncio.gather(t1, t2)
				self.__output_queue.put(_SERVER_OUTPUT_EOF_SENTINEL)

			t1 = asyncio.create_task(drain_reader(proc.stdout, True))
			t2 = asyncio.create_task(drain_reader(proc.stderr, False))
			t3 = asyncio.create_task(set_output_eof())

			await proc.wait()
			try:
				# the process is dead, so the reader drainer tasks should finish too
				await asyncio.wait_for(t3, timeout=1)
			except asyncio.TimeoutError:
				self.logger.warning('run_process() drain_reader wait timeout')

		def do_start() -> _RunningProcess:
			thread = thread_utils.start_thread(asyncio.run, args=(run_process(),), name='ServerProcessManager')
			event_loop: Optional[asyncio.AbstractEventLoop] = None
			try:
				event_loop = event_loop_future.result()
				proc = proc_future.result()
			except Exception:
				if event_loop is not None:
					event_loop.stop()
				raise
			else:
				return _RunningProcess(proc, event_loop, thread)

		event_loop_future: 'cf.Future[asyncio.AbstractEventLoop]' = cf.Future()
		proc_future: 'cf.Future[asyncio.subprocess.Process]' = cf.Future()
		self.__current_process = do_start()

	def read_line(self) -> Optional[ServerOutput]:
		so = self.__output_queue.get()
		if so is _SERVER_OUTPUT_EOF_SENTINEL:
			self.__output_queue.put(so)
			return None
		return so

	def write(self, buf: bytes):
		async def do_write():
			cp.proc.stdin.write(buf)
			await cp.proc.stdin.drain()

		if (cp := self.__current_process) is None:
			raise ProcessNotRunning('process not running')
		if cp.is_proc_alive_and_loop_available():
			asyncio.run_coroutine_threadsafe(do_write(), cp.loop).result()

	def get_wait_future(self) -> 'cf.Future[int]':
		async def do_wait() -> int:
			return await cp.proc.wait()

		if (cp := self.__current_process) is None:
			raise ProcessNotRunning('process not running')
		if cp.is_proc_alive_and_loop_available():
			return asyncio.run_coroutine_threadsafe(do_wait(), cp.loop)
		else:
			future = cf.Future()
			future.set_result(cp.proc.returncode)
			return future

	def send_signal(self, sig: int):
		if (cp := self.__current_process) is None:
			raise ProcessNotRunning('process not running')
		cp.proc.send_signal(sig)

	def is_alive(self) -> bool:
		if cp := self.__current_process:
			return cp.proc.returncode is None
		return False

	def get_pid(self) -> Optional[int]:
		if cp := self.__current_process:
			return cp.proc.pid
		return None

	def get_return_code(self) -> Optional[int]:
		if cp := self.__current_process:
			return cp.proc.returncode
		return None

	def kill_process_tree(self, *, quiet: bool = False):
		proc_pid = self.get_pid()
		if proc_pid is None:
			return

		processes: List[psutil.Process] = []
		with contextlib.suppress(psutil.NoSuchProcess):
			root = psutil.Process(proc_pid)
			processes.append(root)
			processes.extend(root.children(recursive=True))

		# child first, parent last
		for proc in reversed(processes):
			with contextlib.suppress(psutil.NoSuchProcess):
				proc_pid, proc_name = proc.pid, proc.name()
				proc.kill()

				if not quiet:
					self.logger.info(self.__tr('process_killed', proc_name, proc_pid))

	def reset(self):
		if (cp := self.__current_process) is None:
			raise ProcessNotRunning('process not running')
		if cp.proc.returncode is None:
			raise ProcessStillAlive('process is still alive')

		self.__current_process = None
		cp.thread.join(timeout=10)
		if cp.thread.is_alive():
			self.logger.warning('The {} thread is still alive after 10s'.format(cp.thread.name))
			cp.thread.join()

		collection_utils.drain_queue(self.__output_queue)
