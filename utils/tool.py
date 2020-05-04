# -*- coding: utf-8 -*-
import importlib.machinery
import importlib.util
import os
import re
import sys
import threading
from colorama import Fore, Back, Style
from utils import constant


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


def unique_list(l):
	ret = list(set(l))
	ret.sort(key=l.index)
	return ret


def remove_suffix(text, suffix):
	return re.sub(r'{}$'.format(suffix), '', text)


def get_all_base_class(cls):
	if cls is object:
		return []
	ret = [cls]
	for base in cls.__bases__:
		ret.extend(get_all_base_class(base))
	return unique_list(ret)


def clean_minecraft_color_code(text):
	return re.sub('§[\w0-9]', '', str(text))


def clean_console_color_code(text):
	for c in [
		Fore.BLACK, Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN, Fore.WHITE,
		Fore.RESET, Fore.LIGHTBLACK_EX, Fore.LIGHTRED_EX, Fore.LIGHTGREEN_EX, Fore.LIGHTYELLOW_EX,
		Fore.LIGHTBLUE_EX, Fore.LIGHTMAGENTA_EX, Fore.LIGHTCYAN_EX, Fore.LIGHTWHITE_EX,
		Style.BRIGHT, Style.DIM, Style.NORMAL, Style.RESET_ALL,
		Back.BLACK, Back.RED, Back.GREEN, Back.YELLOW, Back.BLUE, Back.MAGENTA, Back.CYAN, Back.WHITE, Back.RESET,
		Back.LIGHTBLACK_EX, Back.LIGHTRED_EX, Back.LIGHTGREEN_EX, Back.LIGHTYELLOW_EX, Back.LIGHTBLUE_EX,
		Back.LIGHTMAGENTA_EX, Back.LIGHTCYAN_EX, Back.LIGHTWHITE_EX
	]:
		text = text.replace(c, '')
	return text


def format_plugin_file_name(file_name):
	file_name = remove_suffix(file_name, constant.DISABLED_PLUGIN_FILE_SUFFIX)
	file_name = remove_suffix(file_name, constant.PLUGIN_FILE_SUFFIX)
	file_name += constant.PLUGIN_FILE_SUFFIX
	return file_name


def format_plugin_file_name_disabled(file_name):
	return format_plugin_file_name(file_name) + constant.DISABLED_PLUGIN_FILE_SUFFIX
