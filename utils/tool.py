# -*- coding: utf-8 -*-
import importlib.machinery
import importlib.util
import os
import re
import sys
import threading


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
		file_path = folder + file
		if os.path.isfile(file_path) and file_path.endswith(suffix):
			ret.append(file_path)
	return ret


def unique_list(l):
	ret = list(set(l))
	ret.sort(key=l.index)
	return ret


def clean_minecraft_color_code(text):
	return re.sub('§[\w0-9]', '', text)
