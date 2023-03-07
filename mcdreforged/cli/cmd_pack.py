import json
import os
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.utils import file_util


def make_packed_plugin(input_dir: str, output_dir: str, file_name: Optional[str], *, quiet: bool = False):
	writeln = print if not quiet else lambda *args, **kwargs: None

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
			meta_dict = json.load(meta_file)  # type: dict
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
	if file_util.get_file_suffix(file_name) not in plugin_constant.PACKED_PLUGIN_FILE_SUFFIXES:
		file_name += plugin_constant.PACKED_PLUGIN_FILE_SUFFIXES[0]
	file_counter = 0

	def write(base_path: str, *, directory_only: bool):
		nonlocal file_counter
		if os.path.isdir(base_path):
			dir_arc = os.path.basename(base_path)
			zip_file.write(base_path, arcname=dir_arc)
			file_counter += 1
			writeln('Creating directory: {} -> {}'.format(base_path, dir_arc))
			for dir_path, dir_names, file_names in os.walk(base_path):
				if os.path.basename(dir_path) == '__pycache__':
					continue
				for file_name_ in file_names + dir_names:
					full_path = os.path.join(dir_path, file_name_)
					if os.path.isdir(full_path) and os.path.basename(full_path) == '__pycache__':
						continue
					arc_name = os.path.join(dir_arc, full_path.replace(base_path, '', 1).lstrip(os.sep))
					zip_file.write(full_path, arcname=arc_name)
					file_counter += 1
					writeln('  Writing: {} -> {}'.format(full_path, arc_name))
		elif os.path.isfile(base_path) and not directory_only:
			arc_name = os.path.basename(base_path)
			zip_file.write(base_path, arcname=arc_name)
			file_counter += 1
			writeln('Writing single file: {} -> {}'.format(base_path, arc_name))
		else:
			writeln('[WARN] {} not found! ignored'.format(base_path))

	writeln('Packing plugin "{}" into "{}" ...'.format(meta.id, file_name))
	with ZipFile(os.path.join(output_dir, file_name), 'w', ZIP_DEFLATED) as zip_file:
		write(meta_file_path, directory_only=False)  # metadata
		write(req_file_path, directory_only=False)  # requirement
		write(os.path.join(input_dir, meta.id), directory_only=True)  # source module
		for resource_path in meta.resources:  # resources
			write(os.path.join(input_dir, resource_path), directory_only=False)

	writeln('Packed {} files/folders into "{}"'.format(file_counter, file_name))
	writeln('Done')
