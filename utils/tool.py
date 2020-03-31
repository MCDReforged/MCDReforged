# -*- coding: utf-8 -*-
import importlib.machinery
import importlib.util
import os
import sys
import threading


def start_thread(func, args, name=None):
	thread = threading.Thread(target=func, args=args)
	thread.setDaemon(True)
	if name is not None:
		thread.setName(name)
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


def list_py_file(folder):
	ret = []
	for file in os.listdir(folder):
		file_path = folder + file
		if os.path.isfile(file_path) and file_path.endswith('.py'):
			ret.append(file_path)
	return ret
