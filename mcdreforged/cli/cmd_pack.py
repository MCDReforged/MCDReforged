import fnmatch
import json
import os
import re
import stat
import zipapp
from typing import Optional, Any, List, Callable, NamedTuple, Pattern
from zipfile import ZipFile, ZIP_DEFLATED

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.utils import file_utils, function_utils

PathPredicate = Callable[[str], bool]


class IgnoreFilter:
	class Pattern(NamedTuple):
		regex: Pattern
		negation: bool
		dir_only: bool

	def __init__(self, patterns: List[str]):
		self.patterns: List[IgnoreFilter.Pattern] = []

		for pattern in patterns:
			pattern = pattern.strip()
			if pattern.startswith("#") or len(pattern) == 0:
				continue

			def add(p: str, dir_only: bool):
				regex_pattern = fnmatch.translate(p)
				regex_pattern = regex_pattern.replace(r'\*\*/', '(?:.+/)?')
				regex_pattern = regex_pattern.replace(r'/\*\*', '(?:/.+)?')
				self.patterns.append(self.Pattern(re.compile(regex_pattern), is_negation, dir_only))

			is_negation = pattern.startswith('!')
			if is_negation:
				pattern = pattern[1:]

			if '/' in pattern[:-1]:  # match from root-dir
				pattern = pattern[1:]
			elif not pattern.startswith('**/'):  # match from any sub-dir
				pattern = '**/' + pattern

			if pattern.endswith('/'):  # yes, it's a dir
				add(pattern[:-1], True)  # ignore the dir itself
				add(pattern + '**', False)  # files inside the dir
			else:
				add(pattern, False)  # ignore the file inside
				add(pattern + '/**', False)  # just in case it's a dir, add everything inside

	def is_ignored(self, path: str):
		path = path.replace(os.sep, '/')
		is_dir = os.path.isdir(path)
		is_ignored = False
		for pattern in self.patterns:
			if pattern.dir_only and not is_dir:
				continue
			if pattern.regex.match(path):
				is_ignored = not pattern.negation
		return is_ignored


def read_ignore_file(file: str, writeln: Callable[[str], Any]) -> Optional[IgnoreFilter]:
	if len(file) == 0:
		return None
	try:
		with open(file, 'r', encoding='utf8') as f:
			lines = f.readlines()
	except Exception as e:
		writeln('Failed to read ignore file {}: {}'.format(file, e))
		return None
	else:
		return IgnoreFilter(lines)


def make_packed_plugin(args: Any, *, quiet: bool = False):
	input_dir: str = args.input
	output_dir: str = args.output
	file_name: Optional[str] = args.name

	writeln = print if not quiet else function_utils.NONE

	if len(args.ignore_patterns) > 0:
		writeln('Using ignore file patterns {}'.format(args.ignore_patterns))
		ignore_filter = IgnoreFilter(args.ignore_patterns)
	else:
		ignore_filter = read_ignore_file(os.path.join(input_dir, args.ignore_file), writeln)
		if ignore_filter is not None:
			writeln('Loaded ignore file patterns from {}'.format(args.ignore_file))
		else:
			ignore_filter = IgnoreFilter([])

	if not os.path.isdir(input_dir):
		writeln('Invalid input directory {}'.format(input_dir))
		return
	if not os.path.isdir(output_dir):
		os.makedirs(output_dir)

	meta_file_path = os.path.join(input_dir, plugin_constant.PLUGIN_META_FILE)
	req_file_path = os.path.join(input_dir, plugin_constant.PLUGIN_REQUIREMENTS_FILE)
	if not os.path.isfile(meta_file_path):
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

	def write(base_path: str, *, directory_only: bool):
		if ignore_filter.is_ignored(base_path):
			return
		nonlocal file_counter
		if os.path.isdir(base_path):
			dir_arc = os.path.basename(base_path)
			zip_file.write(base_path, arcname=dir_arc)
			file_counter += 1
			writeln('Creating directory: {} -> {}'.format(base_path, dir_arc))
			for dir_path, dir_names, file_names in os.walk(base_path):
				for file_name_ in file_names + dir_names:
					full_path = os.path.join(dir_path, file_name_)
					if ignore_filter.is_ignored(full_path):
						continue
					arc_name = os.path.join(dir_arc, full_path.replace(base_path, '', 1).lstrip(os.sep))
					zip_file.write(full_path, arcname=arc_name)
					file_counter += 1
					writeln('  Written: {} -> {}'.format(full_path, arc_name))
		elif os.path.isfile(base_path) and not directory_only:
			arc_name = os.path.basename(base_path)
			zip_file.write(base_path, arcname=arc_name)
			file_counter += 1
			writeln('Writing single file: {} -> {}'.format(base_path, arc_name))
		else:
			writeln('[WARN] {} not found! ignored'.format(base_path))

	writeln('Packing plugin "{}" into "{}" ...'.format(meta.id, file_name))
	packed_plugin_path = os.path.join(output_dir, file_name)
	with open(packed_plugin_path, 'wb') as fd:
		if args.shebang:
			shebang = b'#!' + args.shebang.encode(getattr(zipapp, 'shebang_encoding', 'utf8')) + b'\n'
			fd.write(shebang)
			writeln('Added shebang {}'.format(shebang))

		with ZipFile(fd, 'w', ZIP_DEFLATED) as zip_file:
			write(meta_file_path, directory_only=False)  # metadata
			write(req_file_path, directory_only=False)  # requirement
			write(os.path.join(input_dir, meta.id), directory_only=True)  # source module
			for resource_path in meta.resources:  # resources
				write(os.path.join(input_dir, resource_path), directory_only=False)
	if args.shebang:
		os.chmod(packed_plugin_path, os.stat(packed_plugin_path).st_mode | stat.S_IEXEC)

	writeln('Packed {} files/folders into "{}"'.format(file_counter, file_name))
	writeln('Done')
