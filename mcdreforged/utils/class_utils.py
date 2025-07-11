import importlib
from typing import Any, Type, Union, Iterable, Optional, Collection, TypeVar, List

from mcdreforged.utils import tree_printer, collection_utils

_T = TypeVar('_T')


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


def check_class(class_: Type, base_class: Type, error_message: str = None):
	if not issubclass(class_, base_class):
		if error_message is None:
			error_message = 'Except class derived from {}, but found class {}'.format(base_class, class_)
		raise TypeError(error_message)


def check_type(value: Any, types: Union[Type[_T], Iterable[Type[_T]]], error_message: str = None) -> _T:
	def mapper(x):
		if x is None:
			return type(x)
		return x

	if not isinstance(types, Iterable):
		types = (types,)
	if not isinstance(value, tuple(map(mapper, types))):
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
	def children_getter(c: type):
		return c.__subclasses__()

	def name_getter(c: type) -> str:
		return c.__name__

	tree_printer.print_tree(cls, children_getter, name_getter, line_writer)
