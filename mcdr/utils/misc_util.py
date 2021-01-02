"""
Misc tool collection
"""
import importlib.machinery
import importlib.util
import sys
import threading
from typing import List, Any

from mcdr.plugin.version import Version


def start_thread(func, args, name=None):
	thread = threading.Thread(target=func, args=args, name=name)
	thread.setDaemon(True)
	thread.start()
	return thread


def load_source(path: str, name=None):
	if name is None:
		name = path.replace('/', '_').replace('\\', '_').replace('.', '_')
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[name] = module
	spec.loader.exec_module(module)
	return module


def unique_list(lst: List[Any]) -> List[Any]:
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
