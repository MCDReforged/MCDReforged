import dataclasses
import enum
import queue
import threading
import time
from concurrent.futures import Future
from typing import Dict, Callable, Optional, TYPE_CHECKING, TypeVar, Generic

from mcdreforged.constants import core_constant

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin

_T = TypeVar('_T')


class TaskPriority(enum.Enum):
	HIGH = 0      # for probe tasks
	REGULAR = 1   # for regular tasks
	INFO = 2      # for info tasks
	SENTINEL = 3  # for shutdown sentinel


@dataclasses.dataclass(frozen=True)
class TaskQueueItem(Generic[_T]):
	func: Callable[[], _T]
	priority: TaskPriority
	plugin: Optional['AbstractPlugin']
	future: 'Future[_T]'


class TaskQueue:
	def __init__(self):
		self.__queues: Dict[TaskPriority, 'queue.Queue[TaskQueueItem]'] = {
			TaskPriority.HIGH: queue.Queue(),
			TaskPriority.REGULAR: queue.Queue(maxsize=core_constant.MAX_TASK_QUEUE_SIZE_REGULAR),
			TaskPriority.INFO: queue.Queue(maxsize=core_constant.MAX_TASK_QUEUE_SIZE_INFO),
			TaskPriority.SENTINEL: queue.Queue(),
		}
		for p in TaskPriority:  # ensure the priority range is expected
			_ = self.__queues[p]
		self.__not_empty = threading.Condition(threading.Lock())

	def __len__(self):
		return sum(self.qsizes().values())

	def qsizes(self) -> Dict[TaskPriority, int]:
		return {p: q.qsize() for p, q in self.__queues.items()}

	def put(self, item: TaskQueueItem, block: bool = True, timeout: Optional[float] = None):
		self.__queues[item.priority].put(item, block=block, timeout=timeout)
		with self.__not_empty:
			self.__not_empty.notify()

	def get(self, block: bool = True, timeout: Optional[float] = None) -> TaskQueueItem:
		with self.__not_empty:
			if not block and not len(self):
				raise queue.Empty()

			end_time = time.time() + timeout if timeout is not None else None
			while not len(self):
				remaining = None
				if end_time is not None and (remaining := end_time - time.time()) <= 0:
					raise queue.Empty()
				self.__not_empty.wait(remaining)

			for q in self.__queues.values():
				try:
					return q.get_nowait()
				except queue.Empty:
					pass

			raise AssertionError('should never come here')
