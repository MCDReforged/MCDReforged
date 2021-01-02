"""
Misc tool collection
"""
import importlib.machinery
import importlib.util
import os
import re
import sys
import threading

from mcdr import constant


def start_thread(func, args, name=None):
	thread = threading.Thread(target=func, args=args, name=name)
	thread.setDaemon(True)
	thread.start()
	return thread


def load_source(path, name=None):
	if name is None:
		name = path.replace('/', '_').replace('\\', '_').replace('.', '_')
	spec = importlib.util.spec_from_file_location(name, path)
	module = importlib.util.module_from_spec(spec)
	sys.modules[name] = module
	spec.loader.exec_module(module)
	return module


def list_file(folder, suffix):
	ret = []
	for file in os.listdir(folder):
		file_path = os.path.join(folder, file)
		if os.path.isfile(file_path) and file_path.endswith(suffix):
			ret.append(file_path)
	return ret


def touch_folder(folder):
	if not os.path.isdir(folder):
		os.makedirs(folder)


def unique_list(l):
	ret = list(set(l))
	ret.sort(key=l.index)
	return ret


def remove_suffix(text: str, suffix: str):
	pos = text.rfind(suffix)
	return text[:pos] if pos >= 0 else text


def get_all_base_class(cls):
	if cls is object:
		return []
	ret = [cls]
	for base in cls.__bases__:
		ret.extend(get_all_base_class(base))
	return unique_list(ret)


def clean_minecraft_color_code(text):
	return re.sub('§[a-z0-9]', '', str(text))


def clean_console_color_code(text):
	return re.sub(r'\033\[(\d+(;\d+)?)?m', '', text)


def format_plugin_file_path(file_path):
	file_path = remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
	file_path = remove_suffix(file_path, constant.PLUGIN_FILE_SUFFIX)
	file_path += constant.PLUGIN_FILE_SUFFIX
	return file_path


def format_plugin_file_path_disabled(file_path):
	return format_plugin_file_path(file_path) + constant.DISABLED_PLUGIN_FILE_SUFFIX
