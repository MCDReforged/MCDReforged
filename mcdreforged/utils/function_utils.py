from typing import TypeVar, Callable, Container

from typing_extensions import Protocol

_T = TypeVar('_T')


class _Always(Protocol[_T]):
	def __call__(self, *args, **kwargs) -> _T:
		...


def always(v: _T) -> _Always:
	def func(*_args, **_kwargs) -> _T:
		return v

	return func


def equals(a: _T) -> Callable[[_T], bool]:
	def func(b: _T):
		return a == b

	return func


def not_equals(a: _T) -> Callable[[_T], bool]:
	def func(b: _T):
		return a != b

	return func


def contains(container: Container[_T]) -> Callable[[_T], bool]:
	def func(v: _T):
		return v in container

	return func


TRUE = always(True)
FALSE = always(False)
NONE = always(None)
