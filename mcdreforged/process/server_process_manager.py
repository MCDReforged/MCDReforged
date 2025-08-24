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
from mcdreforged.utils import thread_utils

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


# server stdout and stderr are EOF, and the server process has terminated
_SERVER_OUTPUT_EOF_SENTINEL = ServerOutput(b'', False)


@dataclasses.dataclass(frozen=True)
class _ProcessData:
	process: asyncio.subprocess.Process
	eof_consumed_event: asyncio.Event


@dataclasses.dataclass(frozen=True)
class _RunningProcess:
	thread: threading.Thread
	loop: asyncio.AbstractEventLoop
	output_queue: queue.Queue[ServerOutput]
	proc: asyncio.subprocess.Process
	eof_consumed_event: asyncio.Event

	def is_loop_available(self) -> bool:
		return not self.loop.is_closed() and self.thread.is_alive()

	def is_proc_alive_and_loop_available(self) -> bool:
		return self.proc.returncode is None and self.is_loop_available()


class ServerProcessManager:
	MAX_OUTPUT_QUEUE_SIZE = 1024

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.logger = mcdr_server.logger
		self.__tr = mcdr_server.create_internal_translator('process').tr
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
				sleep_time = min(sleep_time + 0.001, 0.01)
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
				return

			self.logger.mdebug(f'proc created, {proc.pid=}', option=DebugOption.PROCESS)
			eof_consumed_event = asyncio.Event()
			proc_future.set_result(_ProcessData(proc, eof_consumed_event))

			async def handle_output_eof():
				await asyncio.gather(proc.wait(), t1, t2)
				self.logger.mdebug(f'handle_output_eof() proc.wait() and drain_readers finished', option=DebugOption.PROCESS)

				await put_queue(_SERVER_OUTPUT_EOF_SENTINEL)
				self.logger.mdebug(f'handle_output_eof() put EOF ok', option=DebugOption.PROCESS)

				await eof_consumed_event.wait()
				self.logger.mdebug(f'handle_output_eof() EOF consumed', option=DebugOption.PROCESS)

			t1 = asyncio.create_task(drain_reader(proc.stdout, True))
			t2 = asyncio.create_task(drain_reader(proc.stderr, False))
			t3 = asyncio.create_task(handle_output_eof())

			await proc.wait()
			self.logger.mdebug(f'proc.wait() finished, {proc.pid=} {proc.returncode=}', option=DebugOption.PROCESS)

			try:
				# the process is dead, so the reader drainer tasks should finish too
				await asyncio.wait_for(t3, timeout=5)
			except asyncio.TimeoutError:
				self.logger.warning('run_process() handle_output_eof() wait cost too long')
				await t3

		def do_start() -> _RunningProcess:
			thread = thread_utils.start_thread(asyncio.run, args=(run_process(),), name='ServerProcessManager')
			event_loop: Optional[asyncio.AbstractEventLoop] = None
			try:
				event_loop = event_loop_future.result()
				pd = proc_future.result()
			except Exception:
				if event_loop is not None:
					event_loop.stop()
				raise
			else:
				return _RunningProcess(thread, event_loop, output_queue, pd.process, pd.eof_consumed_event)

		event_loop_future: cf.Future[asyncio.AbstractEventLoop] = cf.Future()
		proc_future: cf.Future[_ProcessData] = cf.Future()
		output_queue: queue.Queue[ServerOutput] = queue.Queue(maxsize=self.MAX_OUTPUT_QUEUE_SIZE)
		self.__current_process = do_start()

	def read_line(self) -> Optional[ServerOutput]:
		if (cp := self.__current_process) is not None and cp.is_loop_available():
			so = cp.output_queue.get()
			if so is _SERVER_OUTPUT_EOF_SENTINEL:
				cp.output_queue.put(so)
				cp.loop.call_soon_threadsafe(cp.eof_consumed_event.set)
				return None
			return so
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
