import functools
import json
import os
from pathlib import Path
from typing import Literal, Dict, Callable, Optional, Any, TextIO

from ruamel.yaml import YAML

from mcdreforged.utils import file_utils
from mcdreforged.utils.types.json_like import JsonLike

FileFormat = Literal['json', 'yaml']


class SimpleConfigHandler:
	__DEFAULT_FILE_FORMAT: FileFormat = 'json'
	__FILE_EXTENSIONS: Dict[FileFormat, str] = {
		'json': 'json',
		'yaml': 'yml',
	}

	def __init__(self, file_name: Optional[str], file_format: Optional[FileFormat], parent_dir: str):
		if file_name is None:
			if file_format is None:
				file_format = self.__DEFAULT_FILE_FORMAT
			file_name = 'config.' + self.__FILE_EXTENSIONS[file_format]  # default file name example: "config.json"
		if file_format is None:
			file_format = self.__guess_file_format(file_name)

		if file_format == 'json':
			loader = json.load
			# config file should be nicely readable, so here come the indent and non-ascii chars
			dumper = functools.partial(json.dump, indent=4, ensure_ascii=False)
		elif file_format == 'yaml':
			yaml = YAML(typ='safe')
			yaml.default_flow_style = False  # use block style for yaml
			yaml.width = 1048576
			dumper = yaml.dump
			loader = yaml.load
		else:
			raise ValueError('invalid file_format {!r}'.format(file_format))

		self.__file_name = file_name
		self.__file_path = Path(parent_dir) / self.__file_name
		self.__loader: Callable[[TextIO], JsonLike] = loader
		self.__dumper: Callable[[JsonLike, TextIO], Any] = dumper

	@classmethod
	def __guess_file_format(cls, file_name: str) -> FileFormat:
		ext = os.path.basename(file_name).rsplit('.', 1)[-1]
		if ext in ['json']:
			return 'json'
		elif ext in ['yml', 'yaml']:
			return 'yaml'
		else:
			raise ValueError('cannot detect file format from file path {!r}'.format(file_name))

	def load(self, *, encoding: str) -> JsonLike:
		with open(self.__file_path, encoding=encoding) as file:
			return self.__loader(file)

	def save(self, data: JsonLike, *, encoding: str):
		self.__file_path.parent.mkdir(parents=True, exist_ok=True)
		with file_utils.safe_write(self.__file_path, encoding=encoding) as file:
			self.__dumper(data, file)
