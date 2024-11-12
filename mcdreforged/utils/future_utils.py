import asyncio
import contextlib
from concurrent.futures import Future, CancelledError, TimeoutError
from typing import TypeVar, Optional

_T = TypeVar('_T')


def completed(value: _T) -> 'Future[_T]':
	future = Future()
	future.set_result(value)
	return future


def wait(future: Future, timeout: Optional[float] = None) -> bool:
	"""
	Wait until the given future is done (result set / exception raised / cancelled).
	No exception will be raised from the future

	:return: true if the future is done, false otherwise
	"""
	with contextlib.suppress(CancelledError, TimeoutError):
		future.exception(timeout)
	return future.done()


def copy_done_state(src: 'asyncio.Future[_T]', dst: 'Future[_T]'):
	if src.cancelled():
		dst.cancel()
	elif (exc := src.exception()) is not None:
		dst.set_exception(exc)
	else:
		dst.set_result(src.result())
