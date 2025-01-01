import queue
from typing import List, TypeVar, Iterable

_T = TypeVar('_T')


def unique_list(lst: Iterable[_T]) -> List[_T]:
	return list(dict.fromkeys(lst).keys())


def drain_queue(q: 'queue.Queue[_T]') -> Iterable[_T]:
	while True:
		try:
			yield q.get(block=False)
		except queue.Empty:
			break
