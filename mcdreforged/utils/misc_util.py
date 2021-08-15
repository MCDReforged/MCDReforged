"""
Misc tool collection
"""
import importlib.machinery
import importlib.util
import inspect
import os
import threading
from typing import List, Callable, Tuple, TypeVar, Any, Type, Optional

from mcdreforged.minecraft.rtext import RTextBase
from mcdreforged.plugin.meta.version import Version


def start_thread(func: Callable, args: Tuple, name: str or None = None):
	thread = threading.Thread(target=func, args=args, name=name, daemon=True)
	thread.start()
	return thread


def load_source_from_file_path(source_path: str, module_name=None):
	if not os.path.isfile(source_path):
		raise TypeError('Source path {} is not a file'.format(source_path))
	if module_name is None:
		module_name = source_path.replace('/', '_').replace('\\', '_').replace('.', '_')

	# https://docs.python.org/3/library/importlib.html#importing-a-source-file-directly
	# https://docs.python.org/zh-cn/3.6/library/importlib.html#importing-a-source-file-directly
	spec = importlib.util.spec_from_file_location(module_name, source_path)
	module = importlib.util.module_from_spec(spec)
	# noinspection PyUnresolvedReferences
	spec.loader.exec_module(module)
	# Optional; only necessary if you want to be able to import the module
	# by name later.
	# sys.modules[module_name] = module
	return module


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


def version_compare(v1: str, v2: str) -> int:
	version1 = Version(v1, allow_wildcard=False)
	version2 = Version(v2, allow_wildcard=False)
	return version1.compare_to(version2)


def print_text_to_console(logger, text):
	for line in RTextBase.from_any(text).to_colored_text().splitlines():
		logger.info(line)


def check_type(value: Any, type_: Type, error_message: str = None):
	if not isinstance(value, type_):
		if error_message is None:
			error_message = 'Except type {} but found type {}'.format(type_, type(value))
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
