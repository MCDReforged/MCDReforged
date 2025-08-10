from abc import ABC, ABCMeta, abstractmethod
from typing import Dict, Iterator, TypeVar, Generic, get_type_hints, ClassVar


class NamedObject(ABC):
	@property
	@abstractmethod
	def name(self) -> str:
		"""
		The unique identifier used in :class:`__RRegistry`
		"""
		raise NotImplementedError()


_T = TypeVar('_T', bound=NamedObject)


class RRegistry(ABCMeta, Generic[_T]):
	"""
	Used as a metaclass
	"""
	def __init__(cls, *args, **kwargs):
		super().__init__(*args, **kwargs)
		cls._registry: Dict[str, _T] = {}

	def __iter__(self) -> Iterator[_T]:
		return iter(self._registry.values())

	def __contains__(self, item_name: str) -> bool:
		return item_name in self._registry

	def _get_item(self, name: str) -> _T:
		"""**Not public API**"""
		return self._registry[name]

	def _register_item(self, name: str, item: _T):
		"""**Not public API**"""
		if name != item.name:
			raise AssertionError(f'mismatched name: {name=!r} {item.name=!r}')
		if name in self._registry:
			raise AssertionError(f'already registered: {name=!r} {self._registry[name]=!r}')
		self._registry[name] = item
		setattr(self, name, item)

	def _ensure_registration_done(self):
		"""**Not public API**"""
		for name, annotation in get_type_hints(self).items():
			if getattr(annotation, '__origin__', None) is ClassVar and name not in self._registry:
				raise AssertionError(f'Registry {self} class variable {name!r} has not been registered yet')
