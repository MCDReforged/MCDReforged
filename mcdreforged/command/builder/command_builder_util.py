from typing import Tuple, Optional, TypeVar, Callable

DIVIDER = ' '
"""The char to divide elements in a command string —— space"""


def remove_divider_prefix(text: str) -> str:
	"""
	Remove the element divider prefix of the given text. It's usually used before taking the next element in the command str

	Examples::

		>>> remove_divider_prefix('foo bar')
		'foo bar'
		>>> remove_divider_prefix('  foo bar')
		'foo bar'

	:param text: The text for divider prefix removal
	"""
	return text.lstrip(DIVIDER)


def get_element(text: str) -> str:
	"""
	Get an element from the remaining input

	Examples::

		>>> get_element('foo bar')
		'foo'
		>>> get_element('foo   bar')
		'foo'
		>>> get_element('fooooo')
		'fooooo'
		>>> get_element(' foo')
		''

	:param text: The remaining input to be parsed. It should not start with :data:`DIVIDER`
	"""
	pos = text.find(DIVIDER)
	if pos == -1:
		return text
	else:
		return text[:pos]


T = TypeVar('T')


def __get_var(text: str, func: Callable[[str], T]) -> Tuple[Optional[T], int]:
	"""
	Returns (value, char_read). value will be None if ValueError occurs
	"""
	arg = get_element(text)
	try:
		value = func(arg)
	except ValueError:
		value = None
	return value, len(arg)


def get_int(text: str) -> Tuple[Optional[int], int]:
	"""
	Get an int from the remaining input

	Examples::

		>>> get_int('1234 abc')
		(1234, 4)
		>>> get_int('foo bar')
		(None, 3)
		>>> get_int(' 1234 abc')
		(None, 0)

	:param text: The remaining input to be parsed. It should not start with :data:`DIVIDER`
	:return: a tuple of value, char_read. The value will be None if parsing failed
	"""
	return __get_var(text, int)


def get_float(text: str) -> Tuple[Optional[float], int]:
	"""
	Get a float from the remaining input

	Examples::

		>>> get_float('123.4 abc')
		(123.4, 5)
		>>> get_float('foo bar')
		(None, 3)
		>>> get_int(' 123.4 abc')
		(None, 0)

	:param text: The remaining input to be parsed. It should not start with :data:`DIVIDER`
	:return: a tuple of value, char_read. The value will be None if parsing failed
	"""
	return __get_var(text, float)
