import os
from typing import Callable


def list_all(directory: str, filter: Callable[[str], bool] = lambda file_path: True):
	ret = []
	for file in os.listdir(directory):
		file_path = os.path.join(directory, file)
		if filter(file_path):
			ret.append(file_path)
	return ret


def list_file(directory: str, filter: Callable[[str], bool] = lambda file_path: True):
	return list_all(directory, lambda file_path: os.path.isfile(file_path) and filter(file_path))


def list_file_with_suffix(directory: str, suffix: str):
	return list_file(directory, lambda file_path: file_path.endswith(suffix))


def touch_directory(directory_path: str):
	if not os.path.isdir(directory_path):
		os.makedirs(directory_path)


def get_file_suffix(file_path: str):
	file_name = os.path.basename(file_path)
	index = file_name.rfind('.')
	if index == -1:
		return ''
	return file_name[index:]
