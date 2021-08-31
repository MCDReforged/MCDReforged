"""
Misc tool collection
"""
import importlib
import inspect
import threading
from typing import List, Callable, Tuple, TypeVar, Any, Type, Optional, Union, Iterable

from mcdreforged.minecraft.rtext import RTextBase


def start_thread(func: Callable, args: Tuple, name: Optional[str] = None):
	thread = threading.Thread(target=func, args=args, name=name, daemon=True)
	thread.start()
	return thread


def load_class(path: str):
	"""
	:param path: the path to the class, e.g. mcdreforged.info.Info
	:return: The class
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


T = TypeVar('T')


def unique_list(lst: List[T]) -> List[T]:
	ret = list(set(lst))
	ret.sort(key=lst.index)
	return ret


def get_all_base_class(cls):
	if cls is object:
		return []
	ret = [cls]
	for base in cls.__bases__:
		ret.extend(get_all_base_class(base))
	return unique_list(ret)


def print_text_to_console(logger, text):
	for line in RTextBase.from_any(text).to_colored_text().splitlines():
		logger.info(line)


def check_type(value: Any, types: Union[Type, Iterable[Type]], error_message: str = None):
	if not isinstance(types, Iterable):
		types = [types]
	if not any(map(lambda t: isinstance(value, t), types)):
		if error_message is None:
			error_message = 'Except type {} but found type {}'.format(types, type(value))
		raise TypeError(error_message)


def check_class(class_: Type, base_class: Type, error_message: str = None):
	if not issubclass(class_, base_class):
		if error_message is None:
			error_message = 'Except class derived from {} but found class {}'.format(base_class, class_)
		raise TypeError(error_message)


def copy_signature(target: Callable, origin: Callable) -> Callable:
	"""
	Copy the function signature of origin into target
	"""
	# https://stackoverflow.com/questions/39926567/python-create-decorator-preserving-function-arguments
	target.__signature__ = inspect.signature(origin)
	return target


def represent(obj: Any) -> str:
	"""
	aka repr
	"""
	return '{}[{}]'.format(type(obj).__name__, ','.join([
		'{}={}'.format(k, repr(v)) for k, v in vars(obj).items() if not k.startswith('_')
	]))


class WaitableCallable:
	def __init__(self, func: Callable):
		self.__func = func
		self.__event = threading.Event()

	def __call__(self, *args, **kwargs):
		rv = self.__func(*args, **kwargs)
		self.__event.set()
		return rv

	def wait(self, timeout: Optional[float] = None) -> bool:
		"""
		Return if the event has been set
		"""
		return self.__event.wait(timeout=timeout)