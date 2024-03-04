import contextlib
import os
from pathlib import Path
from typing import Callable, ContextManager, TextIO, Union


def list_all(directory: str, predicate: Callable[[str], bool] = lambda file_path: True):
	caditates = [os.path.join(directory, file) for file in os.listdir(directory)]
	return list(filter(predicate, caditates))


def list_file(directory: str, predicate: Callable[[str], bool] = lambda file_path: True):
	return list_all(directory, lambda file_path: os.path.isfile(file_path) and predicate(file_path))


def list_file_with_suffix(directory: str, suffix: str):
	return list_file(directory, lambda file_path: file_path.endswith(suffix))


def touch_directory(directory_path: Union[str, os.PathLike]):
	if not os.path.isdir(directory_path):
		os.makedirs(directory_path)


def get_file_suffix(file_path: str):
	file_name = os.path.basename(file_path)
	index = file_name.rfind('.')
	if index == -1:
		return ''
	return file_name[index:]


@contextlib.contextmanager
def safe_write(target_file_path: Union[str, Path], *, encoding: str) -> ContextManager[TextIO]:
	if isinstance(target_file_path, str):
		target_file_path = Path(target_file_path)

	temp_file_path = target_file_path.parent / (target_file_path.name + '.tmp')
	with open(temp_file_path, 'w', encoding=encoding) as file:
		yield file
	os.replace(temp_file_path, target_file_path)

