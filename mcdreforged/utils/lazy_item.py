from typing import TypeVar, Callable, Generic

T = TypeVar('T')


class LazyItem(Generic[T]):
	__NONE = object()

	def __init__(self, provider: Callable[[], T]):
		self.__provider = provider
		self.__item = self.__NONE

	def get(self) -> T:
		if self.__item is self.__NONE:
			self.__item = self.__provider()
		return self.__item
