import json
import os
import stat
import zipapp
from pathlib import Path
from typing import Optional, Any, Callable
from zipfile import ZipFile, ZIP_DEFLATED

import pathspec
from typing_extensions import Protocol

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.utils import file_utils, function_utils

PathPredicate = Callable[[str], bool]

class PackArgs(Protocol):
	@property
	def input(self) -> str:
		pass

	@property
	def output(self) -> str:
		pass

	@property
	def name(self) -> str:
		pass

	@property
	def ignore_patterns(self) -> str:
		pass

	@property
	def ignore_file(self) -> str:
		pass

	@property
	def shebang(self) -> str:
		pass


def read_ignore_file(file: Path, writeln: Callable[[str], Any]) -> Optional[pathspec.PathSpec]:
	try:
		with open(file, 'r', encoding='utf8') as f:
			lines = f.readlines()
	except Exception as e:
		writeln('Failed to read ignore file {}: {}'.format(file, e))
		return None
	else:
		return pathspec.GitIgnoreSpec.from_lines(lines)


def make_packed_plugin(args: PackArgs, *, quiet: bool = False):
	input_dir = Path(args.input)
	output_dir = Path(args.output)
	file_name: Optional[str] = args.name

	writeln = print if not quiet else function_utils.NONE
	ignore_filter: Optional[pathspec.PathSpec] = None

	if len(args.ignore_patterns) > 0:
		writeln('Using ignore file patterns {}'.format(args.ignore_patterns))
		ignore_filter = pathspec.GitIgnoreSpec.from_lines(args.ignore_patterns)
	elif args.ignore_file:
		ignore_filter = read_ignore_file(input_dir / args.ignore_file, writeln)
		if ignore_filter is not None:
			writeln('Loaded ignore file patterns from {}'.format(args.ignore_file))
	if ignore_filter is None:
		ignore_filter = pathspec.GitIgnoreSpec.from_lines([])

	if not input_dir.is_dir():
		writeln('Invalid input directory {}'.format(input_dir))
		return
	output_dir.mkdir(exist_ok=True)

	meta_file_path: Path = input_dir / plugin_constant.PLUGIN_META_FILE
	req_file_path: Path = input_dir / plugin_constant.PLUGIN_REQUIREMENTS_FILE
	if not meta_file_path.is_file():
		writeln('Plugin metadata file {} not found'.format(meta_file_path))
		return
	try:
		with open(meta_file_path, encoding='utf8') as meta_file:
			meta_dict: dict = json.load(meta_file)
		assert isinstance(meta_dict, dict)
		meta = Metadata(meta_dict)
	except Exception as e:
		writeln('Fail to load plugin metadata from {}: {}'.format(meta_file_path, e))
		return
	writeln('Plugin ID: {}'.format(meta.id))
	writeln('Plugin version: {}'.format(meta.version))
	if file_name is None:
		file_name = meta.archive_name
	if file_name is None:
		file_name = '{}-v{}'.format(meta.name.replace(' ', '') or meta.id, meta.version)

	file_name = file_name.format(id=meta.id, version=meta.version)
	if file_utils.get_file_suffix(file_name) not in plugin_constant.PACKED_PLUGIN_FILE_SUFFIXES:
		file_name += plugin_constant.PACKED_PLUGIN_FILE_SUFFIXES[0]
	file_counter = 0

	def write(base_path: Path, *, directory_only: bool):
		if ignore_filter.match_file(base_path):
			return
		nonlocal file_counter
		if base_path.is_dir():
			dir_arc = base_path.name
			zip_file.write(base_path, arcname=dir_arc)
			file_counter += 1
			writeln('Creating directory: {} -> {}'.format(base_path, dir_arc))
			for dir_path, dir_names, file_names in os.walk(base_path):
				for file_name_ in file_names + dir_names:
					full_path = Path(dir_path) / file_name_
					if ignore_filter.match_file(full_path):
						continue
					arc_name = os.path.join(dir_arc, full_path.relative_to(base_path))
					zip_file.write(full_path, arcname=arc_name)
					file_counter += 1
					writeln('  Written: {} -> {}'.format(full_path, arc_name))
		elif base_path.is_file() and not directory_only:
			arc_name = base_path.name
			zip_file.write(base_path, arcname=arc_name)
			file_counter += 1
			writeln('Writing single file: {} -> {}'.format(base_path, arc_name))
		else:
			writeln('[WARN] {} not found! ignored'.format(base_path))

	writeln('Packing plugin {!r} into {!r} ...'.format(meta.id, file_name))
	packed_plugin_path = output_dir / file_name
	with open(packed_plugin_path, 'wb') as fd:
		if args.shebang:
			shebang = b'#!' + args.shebang.encode(getattr(zipapp, 'shebang_encoding', 'utf8')) + b'\n'
			fd.write(shebang)
			writeln('Added shebang {}'.format(shebang))

		with ZipFile(fd, 'w', ZIP_DEFLATED) as zip_file:
			write(meta_file_path, directory_only=False)  # metadata
			write(req_file_path, directory_only=False)  # requirement
			write(input_dir / meta.id, directory_only=True)  # source module
			for resource_path in (meta.resources or []):  # resources
				write(input_dir / resource_path, directory_only=False)
	if args.shebang:
		# chmod +x
		os.chmod(packed_plugin_path, os.stat(packed_plugin_path).st_mode | stat.S_IEXEC)

	writeln('Packed {} files/folders into {!r}'.format(file_counter, file_name))
	writeln('Done')
