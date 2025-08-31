import importlib
from typing import Any, Type, Union, Optional, Collection, TypeVar, List, overload, Tuple

from mcdreforged.utils import tree_printer, collection_utils

_T = TypeVar('_T')
_T1 = TypeVar('_T1')
_T2 = TypeVar('_T2')
_T3 = TypeVar('_T3')


def load_class(path: str) -> Any:
	"""
	:param path: the path to the class, e.g. ``mcdreforged.info_reactor.info.Info``
	:return: The class
	:raise ImportError: If load fails
	"""
	try:
		module_path, class_name = path.rsplit('.', 1)
	except ValueError:
		raise ImportError('Wrong path to a class: {}'.format(path)) from None
	module = importlib.import_module(module_path)
	try:
		return getattr(module, class_name)
	except AttributeError:
		raise ImportError('Class {!r} not found in package {!r}'.format(class_name, module_path)) from None


def check_class(class_: Type, base_class: Type, error_message: Optional[str] = None):
	if not issubclass(class_, base_class):
		if error_message is None:
			error_message = 'Except class derived from {}, but found class {}'.format(base_class, class_)
		raise TypeError(error_message)


@overload
def check_type(value: Any, types: Type[_T], error_message: Optional[str] = None) -> _T:
	...


@overload
def check_type(value: Any, types: None, error_message: Optional[str] = None) -> None:
	...


@overload
def check_type(value: Any, types: Tuple[Type[_T1], Type[_T2]], error_message: Optional[str] = None) -> Union[_T1, _T2]:
	...


@overload
def check_type(value: Any, types: Tuple[None, Type[_T2]], error_message: Optional[str] = None) -> Union[None, _T2]:
	...


@overload
def check_type(value: Any, types: Tuple[Type[_T1], None], error_message: Optional[str] = None) -> Union[_T1, None]:
	...


@overload
def check_type(value: Any, types: Tuple[Type[_T1], Type[_T2], Type[_T3]], error_message: Optional[str] = None) -> Union[_T1, _T2, _T3]:
	...


@overload
def check_type(value: Any, types: Tuple[None, Type[_T2], Type[_T3]], error_message: Optional[str] = None) -> Union[None, _T2, _T3]:
	...


@overload
def check_type(value: Any, types: Tuple[Type[_T1], None, Type[_T3]], error_message: Optional[str] = None) -> Union[_T1, None, _T3]:
	...


@overload
def check_type(value: Any, types: Tuple[Type[_T1], Type[_T2], None], error_message: Optional[str] = None) -> Union[_T1, _T2, None]:
	...


@overload
def check_type(value: Any, types: Tuple[Type], error_message: Optional[str] = None) -> Any:  # whatever
	...


def check_type(value: Any, types: Any, error_message: Optional[str] = None) -> Any:
	def type_mapper(x: Union[Type, None]) -> Type:
		if x is None:
			return type(x)
		return x

	if isinstance(types, Collection):
		types = tuple(types)
	else:
		types = (types,)
	if not isinstance(value, tuple(map(type_mapper, types))):
		if error_message is None:
			error_message = 'Except type {}, but found type {}'.format(types[0] if len(types) == 1 else types, type(value))
		raise TypeError(error_message)
	return value


def get_all_base_class(cls: Type) -> List[Type]:
	if cls is object:
		return []
	ret = [cls]
	for base in cls.__bases__:
		ret.extend(get_all_base_class(base))
	return collection_utils.unique_list(ret)


def represent(obj: Any, fields: Optional[dict] = None, *, blacklist: Collection[str] = (), parentheses: str = '()') -> str:
	"""
	aka repr
	"""
	if fields is None:
		fields = {k: v for k, v in vars(obj).items() if not k.startswith('_')}
	blacklist = set(blacklist)
	return ''.join([
		type(obj).__name__,
		parentheses[0],
		', '.join([
			f'{k}={v!r}'
			for k, v in fields.items()
			if k not in blacklist
		]),
		parentheses[1],
	])


def print_class_inheriting_tree(cls: Type, line_writer: tree_printer.LineWriter = print):
	"""
	Remember to import all subclasses before invoking this
	"""
	def children_getter(c: Type):
		return c.__subclasses__()

	def name_getter(c: Type) -> str:
		return c.__name__

	tree_printer.print_tree(cls, children_getter, name_getter, line_writer)
