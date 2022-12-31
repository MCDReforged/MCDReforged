"""
Misc tool collection
"""
import inspect
import threading
from typing import List, Callable, Tuple, TypeVar, Any, Optional, Iterable


def start_thread(func: Callable, args: Tuple, name: Optional[str] = None):
	thread = threading.Thread(target=func, args=args, name=name, daemon=True)
	thread.start()
	return thread


T = TypeVar('T')


def unique_list(lst: Iterable[T]) -> List[T]:
	return list(dict.fromkeys(lst).keys())


def print_text_to_console(logger, text: Any):
	from mcdreforged.minecraft.rtext.text import RTextBase
	for line in RTextBase.from_any(text).to_colored_text().splitlines():
		logger.info(line)


def copy_signature(target: Callable, origin: Callable) -> Callable:
	"""
	Copy the function signature of origin into target
	"""
	assert callable(target) and callable(origin)

	# https://stackoverflow.com/questions/39926567/python-create-decorator-preserving-function-arguments
	target.__signature__ = inspect.signature(origin)
	return target


class WaitableCallable:
	def __init__(self, func: Callable):
		self.__func = func
		self.__event = threading.Event()

	def __call__(self, *args, **kwargs):
		rv = self.__func(*args, **kwargs)
		self.__event.set()
		return rv

	def wait(self, timeout: Optional[float] = None) -> bool:
		"""
		Return if the event has been set
		"""
		return self.__event.wait(timeout=timeout)
