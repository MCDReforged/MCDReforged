import os
import shlex
import subprocess
import tempfile
from argparse import ArgumentParser, Namespace
from typing import Callable
from typing import Optional, List
from zipfile import ZipFile

from typing_extensions import NoReturn

import sys
from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.installer.plugin_installer import PluginInstaller
from mcdreforged.plugin.installer.replier import NoopReplier, StdoutReplier


def create(parser_factory: Callable[..., ArgumentParser]) -> ArgumentParser:
	parser = parser_factory(name='pim', help='Plugin Installer for MCDReforged')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='pim_command')

	subparsers.add_parser('test', help='test command')

	parser_list = subparsers.add_parser('list', help='List plugin from the official plugin catalogue')
	parser_list.add_argument('keyword', nargs='?', default=None, help='Search keyword to filter the plugins')

	parser_download = subparsers.add_parser('download', help='Download given plugins. By default, no dependency resolution will be made')
	parser_download.add_argument('plugin_ids', nargs='+', help='Plugin IDs to be downloaded')
	parser_download.add_argument('-o', '--output', default='.', help='Path to store the downloaded plugins')
	parser_download.add_argument('-d', '--dependencies', action='store_true', help='If dependencies of the given plugins should also be downloaded')

	parser_pipi = subparsers.add_parser('pipi', help='Call "pip install" with the requirements.txt file in the given packed plugin to install Python packages')
	parser_pipi.add_argument('plugin_paths', nargs='+', help='The packed plugin files to be processed')
	parser_pipi.add_argument('-a', '--args', help='Extra arguments passing to the pip process, e.g. --args "--proxy http://localhost:8080", --args "-i https://pypi.org/simple/"')

	return parser


def __entry(parser: ArgumentParser, args: Namespace) -> int:
	pcmd = args.pim_command

	if pcmd is None:
		parser.print_help()
		return 1

	replier = NoopReplier() if args.quiet else StdoutReplier()
	installer = PluginInstaller(replier)

	if pcmd == 'test':
		return installer.test_stuffs()
	elif pcmd == 'list':
		return installer.list_plugin(keyword=args.keyword)
	elif pcmd == 'download':
		return installer.download_plugin(args.plugin_ids, args.output)
	elif pcmd == 'pipi':
		pip_install_from_plugins(args.plugin_paths, extra_args=args.args, quiet=args.quiet)
	else:
		print('unknown pcmd {!r}'.format(pcmd))
		return 1


def entry(parser: ArgumentParser, args: Namespace) -> NoReturn:
	sys.exit(__entry(parser, args))


def pip_install_from_plugins(plugin_paths: List[str], extra_args: Optional[str] = None, *, quiet: bool = False) -> int:
	writeln = print if not quiet else lambda *args_, **kwargs_: None

	# read requirements.txt
	requirement_lines: List[bytes] = []
	req_file_name = plugin_constant.PLUGIN_REQUIREMENTS_FILE
	for plugin_path in plugin_paths:
		try:
			with ZipFile(plugin_path) as zip_file:
				if req_file_name not in zip_file.namelist():
					writeln('Plugin {!r} does not contain a {}'.format(plugin_path, req_file_name))
					return 1
				requirement_lines.extend(zip_file.read(req_file_name).splitlines())
		except Exception as e:
			writeln('Failed to read plugin from {!r}: {}'.format(plugin_path, e))
			return 2

	writeln('Installing requirements from {}'.format(', '.join(plugin_paths)))
	subprocess.call([sys.executable, '-m', 'pip', '-V'])

	temp_file = None
	try:
		# cannot set delete=True, or pip cannot access it
		with tempfile.NamedTemporaryFile(delete=False) as temp_file:
			temp_file.write(b'\n'.join(requirement_lines))
			temp_file.flush()

		args = [sys.executable, '-m', 'pip', 'install', '-r', temp_file.name]
		if extra_args is not None:
			args.extend(shlex.split(extra_args))
		if quiet:
			args.append('-q')

		ret = subprocess.call(args)
		if ret == 0:
			writeln('Pip install succeeded')
		else:
			writeln('Pip process failed with return code {}'.format(ret))
	finally:
		if temp_file is not None:
			try:
				os.unlink(temp_file.name)
			except OSError:
				pass

	return 0
