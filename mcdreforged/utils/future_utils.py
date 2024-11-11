from concurrent.futures import Future
from typing import TypeVar

_T = TypeVar('_T')


def completed(value: _T) -> Future[_T]:
	future = Future()
	future.set_result(value)
	return future
