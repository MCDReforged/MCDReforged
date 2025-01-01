from typing import List, TypeVar, Iterable

_T = TypeVar('_T')


def unique_list(lst: Iterable[_T]) -> List[_T]:
	return list(dict.fromkeys(lst).keys())
