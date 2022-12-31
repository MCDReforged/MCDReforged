import importlib
from typing import Any, Type, Union, Iterable

from mcdreforged.utils import misc_util, tree_printer


def load_class(path: str):
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
		raise ImportError('Class "{}" not found in package "{}"'.format(class_name, module_path)) from None


def check_class(class_: Type, base_class: Type, error_message: str = None):
	if not issubclass(class_, base_class):
		if error_message is None:
			error_message = 'Except class derived from {}, but found class {}'.format(base_class, class_)
		raise TypeError(error_message)


def check_type(value: Any, types: Union[Type, Iterable[Type]], error_message: str = None):
	def mapper(x):
		if x is None:
			return type(x)
		return x

	if not isinstance(types, Iterable):
		types = (types,)
	if not isinstance(value, tuple(map(mapper, types))):
		if error_message is None:
			error_message = 'Except type {}, but found type {}'.format(types, type(value))
		raise TypeError(error_message)


def get_all_base_class(cls):
	if cls is object:
		return []
	ret = [cls]
	for base in cls.__bases__:
		ret.extend(get_all_base_class(base))
	return misc_util.unique_list(ret)


def represent(obj: Any) -> str:
	"""
	aka repr
	"""
	return '{}[{}]'.format(type(obj).__name__, ','.join([
		'{}={}'.format(k, repr(v)) for k, v in vars(obj).items() if not k.startswith('_')
	]))


def print_class_inheriting_tree(cls: Type, line_writer: tree_printer.LineWriter = print):
	"""
	Remember to import all subclasses before invoking this
	"""
	tree_printer.print_tree(
		cls,
		lambda c: c.__subclasses__(),
		lambda c: c.__name__,
		line_writer
	)
