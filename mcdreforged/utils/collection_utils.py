import asyncio
import queue
from typing import List, TypeVar, Iterable, Union

_T = TypeVar('_T')


def unique_list(lst: Iterable[_T]) -> List[_T]:
	return list(dict.fromkeys(lst).keys())


def drain_iterate_queue(q: Union[queue.Queue[_T], asyncio.Queue[_T]]) -> Iterable[_T]:
	while True:
		try:
			yield q.get_nowait()
		except (queue.Empty, asyncio.QueueEmpty):
			break


def drain_queue(q: Union[queue.Queue[_T], asyncio.Queue[_T]]):
	for _ in drain_iterate_queue(q):
		pass
