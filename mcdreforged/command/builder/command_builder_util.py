from typing import Tuple, Optional, TypeVar, Callable

DIVIDER = ' '


def remove_divider_prefix(text: str) -> str:
	return text.lstrip(DIVIDER)


def get_element(text: str) -> str:
	"""
	"my test command" -> "my"
	:type text: str
	:rtype: str
	"""
	pos = text.find(DIVIDER)
	if pos == -1:
		return text
	else:
		return text[:pos]


T = TypeVar('T')


def __get_var(text: str, func: Callable[[str], T]) -> Tuple[Optional[T], int]:
	"""
	Return value, char_read
	value will be None if ValueError occurs
	"""
	arg = get_element(text)
	try:
		value = func(arg)
	except ValueError:
		value = None
	return value, len(arg)


def get_int(text: str) -> Tuple[Optional[int], int]:
	return __get_var(text, int)


def get_float(text: str) -> Tuple[Optional[float], int]:
	return __get_var(text, float)
