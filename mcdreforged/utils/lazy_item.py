from typing import TypeVar, Callable, Generic, Any

_T = TypeVar('_T')


class LazyItem(Generic[_T]):
	__NONE: Any = object()

	def __init__(self, provider: Callable[[], _T]):
		self.__provider = provider
		self.__item: _T = self.__NONE

	def get(self) -> _T:
		if self.__item is self.__NONE:
			self.__item = self.__provider()
		return self.__item
