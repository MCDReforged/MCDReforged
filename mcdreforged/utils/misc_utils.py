"""
Misc tool collection
"""
import inspect
import logging
import threading
from typing import List, Callable, Tuple, TypeVar, Any, Optional, Iterable


def start_thread(func: Callable, args: Tuple, name: Optional[str] = None):
	thread = threading.Thread(target=func, args=args, name=name, daemon=True)
	thread.start()
	return thread


T = TypeVar('T')


def unique_list(lst: Iterable[T]) -> List[T]:
	return list(dict.fromkeys(lst).keys())


def print_text_to_console(logger: logging.Logger, text: Any):
	from mcdreforged.minecraft.rtext.text import RTextBase
	text_str = RTextBase.from_any(text).to_colored_text()
	if len(text_str) == 0:
		logger.info(text_str)
	else:
		for line in text_str.splitlines():
			logger.info(line)


def copy_signature(target: Callable, origin: Callable) -> Callable:
	"""
	Copy the function signature of origin into target
	"""
	assert callable(target) and callable(origin)

	# https://stackoverflow.com/questions/39926567/python-create-decorator-preserving-function-arguments
	target.__signature__ = inspect.signature(origin)
	return target

