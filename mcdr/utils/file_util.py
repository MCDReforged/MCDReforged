import os
from typing import Callable


def list_file(folder: str, filter: Callable[[str], bool] = lambda file_path: True):
	ret = []
	for file in os.listdir(folder):
		file_path = os.path.join(folder, file)
		if os.path.isfile(file_path) and filter(file_path):
			ret.append(file_path)
	return ret


def list_file_with_suffix(folder: str, suffix: str):
	return list_file(folder, lambda file_path: file_path.endswith(suffix))


def touch_folder(folder):
	if not os.path.isdir(folder):
		os.makedirs(folder)
