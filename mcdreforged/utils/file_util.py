import os
from typing import Callable


def list_file(directory: str, filter: Callable[[str], bool] = lambda file_path: True):
	ret = []
	for file in os.listdir(directory):
		file_path = os.path.join(directory, file)
		if os.path.isfile(file_path) and filter(file_path):
			ret.append(file_path)
	return ret


def list_file_with_suffix(directory: str, suffix: str):
	return list_file(directory, lambda file_path: file_path.endswith(suffix))


def touch_directory(directory):
	if not os.path.isdir(directory):
		os.makedirs(directory)
