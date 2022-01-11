import os
import sys
import subprocess
import re
import json
from argparse import ArgumentParser
from typing import Optional
from zipfile import ZipFile, ZIP_DEFLATED

from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.utils import file_util

try:
	from mcdreforged.constants import core_constant, plugin_constant
	from mcdreforged.mcdr_server import MCDReforgedServer
except ModuleNotFoundError:
	print('It seems that you have not installed all require modules')
	raise


def environment_check():
	python_version = sys.version_info.major + sys.version_info.minor * 0.1
	if python_version < 3.6:
		print('Python 3.6+ is needed')
		raise Exception('Python version {} is too old'.format(python_version))


def entry_point():
	environment_check()
	if len(sys.argv) == 1:
		run_mcdr()
		return

	parser = ArgumentParser(
		prog=core_constant.PACKAGE_NAME,
		description='{} CLI'.format(core_constant.NAME),
	)
	parser.add_argument('-q', '--quiet', help='Disable CLI output', action='store_true')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='subparser_name')

	subparsers.add_parser('start', help='Start {}'.format(core_constant.NAME))
	subparsers.add_parser('init', help='Prepare the working environment of {}. Create commonly used folders and generate default configure and permission files'.format(core_constant.NAME))
	subparsers.add_parser('gendefault', help='Generate default configure and permission files at current working directory. Existed files will be overwritten')

	parser_pack = subparsers.add_parser('pack', help='Pack plugin files into a packed plugin')
	parser_pack.add_argument('-i', '--input', help='The input directory which the plugin is in, default: current directory', default='.')
	parser_pack.add_argument('-o', '--output', help='The output directory to store the zipped plugin, default: current directory', default='.')
	parser_pack.add_argument('-n', '--name', help='A specific name to the output zipped plugin file. If not given the metadata specific name or a default one will be used', default=None)

	parser_workspace = subparsers.add_parser('init_plugin', help='Initialize a plugin workspace')
	parser_workspace.add_argument('-p', '--path',         help='The plugin path, default: current directory',        default=None)
	parser_workspace.add_argument('-i', '--id',           help="The plugin id",                                      default=None)
	parser_workspace.add_argument('-n', '--name',         help="The plugin name, default: as same as the plugin id", default=None)
	parser_workspace.add_argument('-d', '--description',  help="The plugin description",                             default=None)
	parser_workspace.add_argument('-a', '--author',       help="The plugin author(s), split with ':'",               default=None)
	parser_workspace.add_argument('-l', '--link',         help="The plugin link",                                    default=None)
	parser_workspace.add_argument('-r', '--resources',    help="The plugin resources files, split with ':'",         default=None)
	parser_workspace.add_argument('-e', '--entrypoint',   help="The plugin's entry point",                           default=None)
	parser_workspace.add_argument('-A', '--archive-name', help="The plugin's archive name",                          default=None)

	result = parser.parse_args()
	quiet = result.quiet

	if result.subparser_name == 'start':
		run_mcdr()
	elif result.subparser_name == 'init':
		initialize_environment(quiet=quiet)
	elif result.subparser_name == 'gendefault':
		generate_default_stuffs(quiet=quiet)
	elif result.subparser_name == 'pack':
		make_packed_plugin(result.input, result.output, result.name, quiet=quiet)
	elif result.subparser_name == 'init_plugin':
		try:
			init_plugin_workspace(result.path, result.id, result.name, result.description, result.author, result.link, result.resources, result.entrypoint, result.archive_name, quiet=quiet)
		except KeyboardInterrupt as e:
			print('signal: interrupt')

def run_mcdr():
	print('{} {} is starting up'.format(core_constant.NAME, core_constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(core_constant.NAME, core_constant.GITHUB_URL))
	try:
		mcdreforged_server = MCDReforgedServer()
	except:
		print('Fail to initialize {}'.format(core_constant.NAME_SHORT))
		raise
	else:
		if mcdreforged_server.is_initialized():
			mcdreforged_server.start()
		else:
			# If it's not initialized, config file or permission file is missing
			# Just dont do anything to let the user to check the files
			pass


def initialize_environment(*, quiet: bool = False):
	MCDReforgedServer(initialize_environment=True)
	if not quiet:
		print('Initialized environment for {} in {}'.format(core_constant.NAME, os.getcwd()))


def generate_default_stuffs(*, quiet: bool = False):
	MCDReforgedServer(generate_default_only=True)
	if not quiet:
		print('Generated default configure and permission files in {}'.format(os.getcwd()))


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
					arc_name = os.path.join(os.path.basename(base_path), full_path.replace(base_path, '', 1).lstrip(os.sep))
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

def init_plugin_workspace(path: str, pid: str, name: str, description: str, authors: str, link: str, resources: str, entrypoint: str, archive_name: str, *, quiet: bool = False):
	writeln = print if not quiet else lambda *args, **kwargs: None
	if quiet:
		def ask(*args, default=None, **kwargs):
			return default
	else:
		def ask(msg, *, default=None, skip=False):
			r = input(('{} (enter to skip): ' if skip else '{}: ' if default is None else '{0} (default "{1}"): ').format(msg, default))
			return default if len(r) == 0 else r

	if path is None:
		path = ask('Plugin workspace', default='.')
	metafile = os.path.join(path, plugin_constant.PLUGIN_META_FILE)
	if os.path.exists(metafile):
		writeln('[ERROR] Meta file "{}" already exists'.format(metafile))
		sys.exit(1)

	if pid is None:
		pid = ask('Id', default=os.path.basename(os.path.abspath(path)).lower()).strip()
	if re.fullmatch(r'[0-9a-z_]{1,64}', pid) is None:
		writeln('[ERROR] Plugin ID "{}" is invalid (match express: [0-9a-z_]{{1,64}})'.format(pid))
		sys.exit(1)

	if name is None:
		name = ask('Name', default=pid).strip()

	if description is None:
		description = ask('Description', default='This is a plugin for MCDR').strip()

	if authors is None:
		authors = ask("Author(s), split with ':'")

	if link is None:
		link = ask('Main page link', skip=True)

	if resources is None:
		resources = ask("Resource(s), split with ':'", skip=True)

	if entrypoint is None:
		entrypoint = ask('Entry point', skip=True)

	if entrypoint is not None and entrypoint != pid and not entrypoint.startswith(pid + '.'):
		writeln('Invalid entry point "{0}" for plugin id "{1}"'.format(entrypoint, pid))
		sys.exit(1)

	if archive_name is None:
		archive_name = ask('Archive name', skip=True)

	metadata = {
		'id': pid,
		'version': '1.0.0',
		'name': name,
		'description': description,
		'dependencies': {
			'mcdreforged': '>=2.0.0'
		}
	}
	if entrypoint is not None:
		metadata['entrypoint'] = entrypoint
	if authors is not None:
		metadata['author'] = list(set((a.strip() for a in authors.split(':'))))
	if link is not None:
		metadata['link'] = link
	if resources is not None:
		metadata['resources'] = list(set(resources.split(':')))
	if archive_name is not None:
		metadata['archive_name'] = archive_name

	with open(metafile, 'w', encoding='utf8') as fd:
		json.dump(metadata, fd, indent=4)
		writeln('Created meta file "{}"'.format(metafile))

	with open(os.path.join(path, 'requirements.txt'), 'w', encoding='utf8') as fd:
		fd.write('# Add your python package requirements here, just like regular requirements.txt\n')

	if entrypoint is None:
		entry, point = (pid, '__init__')
	else:
		entry, point = entrypoint.rsplit('.', 1)
		entry = pid if len(entry) == 0 else entry.replace('.', os.sep)
	if not os.path.exists(os.path.join(path, entry)):
		os.makedirs(os.path.join(path, entry))
	entrypointf = os.path.join(path, entry, point + '.py')
	with open(entrypointf, 'w', encoding='utf8') as fd:
		fd.write('# Write your codes here\n')
		writeln('Created entrypoint "{}"'.format(entrypointf))

