import contextlib
import os
from pathlib import Path
from typing import Callable, ContextManager, TextIO, Union, List

from mcdreforged.utils.types.path_like import PathLike


def list_all(directory: PathLike, predicate: Callable[[Path], bool] = lambda file_path: True) -> List[Path]:
	directory = Path(directory)
	caditates = [(directory / file) for file in os.listdir(directory)]
	return list(filter(predicate, caditates))


def list_file(directory: PathLike, predicate: Callable[[Path], bool] = lambda file_path: True) -> List[Path]:
	def merged_predicate(p: Path) -> bool:
		return p.is_file() and predicate(p)
	return list_all(directory, merged_predicate)


def list_file_with_suffix(directory: PathLike, suffix: str) -> List[Path]:
	def predicate(p: Path) -> bool:
		return p.name.endswith(suffix)
	return list_file(directory, predicate)


def touch_directory(directory_path: PathLike) -> None:
	if not os.path.isdir(directory_path):
		os.makedirs(directory_path, exist_ok=True)


def get_file_suffix(file_path: Union[str, Path]) -> str:
	if isinstance(file_path, Path):
		file_name = file_path.name
	else:
		file_name = os.path.basename(file_path)
	index = file_name.rfind('.')
	if index == -1:
		return ''
	return file_name[index:]


@contextlib.contextmanager
def safe_write(target_file_path: PathLike, *, encoding: str) -> ContextManager[TextIO]:
	target_file_path = Path(target_file_path)
	temp_file_path = target_file_path.parent / (target_file_path.name + '.tmp')
	with open(temp_file_path, 'w', encoding=encoding) as file:
		yield file
	os.replace(temp_file_path, target_file_path)

