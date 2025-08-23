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

from mcdreforged.logging.debug_option import DebugOption
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
	thread: threading.Thread
	loop: asyncio.AbstractEventLoop
	proc: asyncio.subprocess.Process
	output_queue: queue.Queue[ServerOutput]

	def is_loop_available(self) -> bool:
		return not self.loop.is_closed() and self.thread.is_alive()

	def is_proc_alive_and_loop_available(self) -> bool:
		return self.proc.returncode is None and self.is_loop_available()


class ServerProcessManager:
	MAX_OUTPUT_QUEUE_SIZE = 1024

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.logger = mcdr_server.logger
		self.__tr = mcdr_server.create_internal_translator('process').tr
		self.__remaining_outputs: 'queue.Queue[ServerOutput]' = queue.Queue(maxsize=self.MAX_OUTPUT_QUEUE_SIZE * 5)
		self.__has_remaining_outputs = False
		self.__current_process: Optional[_RunningProcess] = None

	def __del__(self):
		if self.is_alive():
			with contextlib.suppress(Exception):
				self.kill_process_tree(quiet=True)

	def start(self, args: Union[str, List[str]], cwd: Path):
		if self.__current_process is not None:
			raise ProcessAlreadyRunning('server process already started')

		async def put_queue(so: ServerOutput):
			sleep_time = 0
			while True:
				try:
					output_queue.put_nowait(so)
					break
				except queue.Full:
					pass
				sleep_time = max(sleep_time + 0.001, 0.01)
				await asyncio.sleep(sleep_time)

		async def drain_reader(reader: asyncio.StreamReader, is_stdout: bool):
			self.logger.mdebug(f'drain_reader() start {is_stdout=}', option=DebugOption.PROCESS)
			queue_full_warn_ts = 0
			while line := await reader.readline():
				await put_queue(ServerOutput(line, is_stdout))
				if output_queue.full():
					now = time.time()
					if now - queue_full_warn_ts >= 10:
						queue_full_warn_ts = now
						self.logger.warning('output queue is full')
			self.logger.mdebug(f'drain_reader() end {is_stdout=}', option=DebugOption.PROCESS)

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

			self.logger.mdebug(f'proc created, {proc.pid=}', option=DebugOption.PROCESS)
			proc_future.set_result(proc)

			async def set_output_eof():
				await asyncio.gather(proc.wait(), t1, t2)
				await put_queue(_SERVER_OUTPUT_EOF_SENTINEL)

			t1 = asyncio.create_task(drain_reader(proc.stdout, True))
			t2 = asyncio.create_task(drain_reader(proc.stderr, False))
			t3 = asyncio.create_task(set_output_eof())

			await proc.wait()
			self.logger.mdebug(f'proc.wait() finished, {proc.pid=} {proc.returncode=}', option=DebugOption.PROCESS)

			try:
				# the process is dead, so the reader drainer tasks should finish too
				await asyncio.wait_for(t3, timeout=5)
			except asyncio.TimeoutError:
				self.logger.warning('run_process() drain_reader wait cost too long')
				await t3
			self.logger.mdebug(f'set_output_eof() finished, {output_queue.qsize()=}', option=DebugOption.PROCESS)

			for so in collection_utils.drain_iterate_queue(output_queue):
				if so is _SERVER_OUTPUT_EOF_SENTINEL:
					continue
				try:
					self.__remaining_outputs.put_nowait(so)
					self.__has_remaining_outputs = True
				except queue.Full:
					self.logger.warning('self.__remaining_outputs is full, discarding {} remaining output_queue items'.format(output_queue.qsize()))

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
				return _RunningProcess(thread, event_loop, proc, output_queue)

		event_loop_future: cf.Future[asyncio.AbstractEventLoop] = cf.Future()
		proc_future: cf.Future[asyncio.subprocess.Process] = cf.Future()
		output_queue = queue.Queue(maxsize=self.MAX_OUTPUT_QUEUE_SIZE)
		self.__current_process = do_start()

	def read_line(self) -> Optional[ServerOutput]:
		if self.__has_remaining_outputs:
			try:
				return self.__remaining_outputs.get_nowait()
			except queue.Empty:
				self.__has_remaining_outputs = False

		def do_read_line() -> Optional[ServerOutput]:
			so = cp.output_queue.get()
			if so is _SERVER_OUTPUT_EOF_SENTINEL:
				cp.output_queue.put(so)
				return None
			return so

		if (cp := self.__current_process) is not None and cp.is_loop_available():
			return do_read_line()
		else:
			return None

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

		cp.thread.join(timeout=10)
		if cp.thread.is_alive():
			self.logger.warning('The {} thread is still alive after 10s'.format(cp.thread.name))
			cp.thread.join()
		self.__current_process = None
