import contextlib
import hashlib
import os
from pathlib import Path
from typing import Callable, TextIO, Union, List, Generator, BinaryIO, Optional, Any

from mcdreforged.utils import function_utils
from mcdreforged.utils.types.path_like import PathStr


def list_all(directory: PathStr, predicate: Callable[[Path], bool] = function_utils.TRUE) -> List[Path]:
	directory = Path(directory)
	candidates = [(directory / file) for file in os.listdir(directory)]
	return list(filter(predicate, candidates))


def list_file(directory: PathStr, predicate: Callable[[Path], bool] = function_utils.TRUE) -> List[Path]:
	def merged_predicate(p: Path) -> bool:
		return p.is_file() and predicate(p)
	return list_all(directory, merged_predicate)


def list_file_with_suffix(directory: PathStr, suffix: str) -> List[Path]:
	def predicate(p: Path) -> bool:
		return p.name.endswith(suffix)
	return list_file(directory, predicate)


def touch_directory(directory_path: PathStr) -> None:
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
def __safe_write(target_file_path: PathStr, mode: str, encoding: Optional[str]) -> Generator[Any, None, None]:
	target_file_path = Path(target_file_path)
	temp_file_path = target_file_path.parent / (target_file_path.name + '.tmp')
	with open(temp_file_path, mode, encoding=encoding) as file:
		yield file
	os.replace(temp_file_path, target_file_path)


@contextlib.contextmanager
def safe_write(target_file_path: PathStr, *, encoding: str) -> Generator[TextIO, None, None]:
	with __safe_write(target_file_path, mode='w', encoding=encoding) as file:
		yield file


@contextlib.contextmanager
def safe_write_b(target_file_path: PathStr) -> Generator[BinaryIO, None, None]:
	with __safe_write(target_file_path, mode='wb', encoding=None) as file:
		yield file


def calc_file_sha256(file_path: PathStr) -> str:
	hasher = hashlib.sha256()
	with open(file_path, 'rb') as f:
		while buf := f.read(16 * 1024):
			hasher.update(buf)
	return hasher.hexdigest()
