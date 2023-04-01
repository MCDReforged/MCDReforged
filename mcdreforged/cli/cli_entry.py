import platform
import sys
from argparse import ArgumentParser

from mcdreforged.constants import core_constant


def environment_check():
	"""
	This should even work in python2.7+
	"""
	def print_stderr(text):
		sys.stderr.write(text + '\n')

	python_version = sys.version_info.major + sys.version_info.minor * 0.1
	if python_version < 3.6:
		print_stderr('Python 3.6+ is needed to run {}'.format(core_constant.NAME))
		print('Current Python version {} is too old'.format(platform.python_version()))
		sys.exit(1)
	if python_version < 3.8:
		print_stderr("Notice: {} will drop the support for Python <=3.7 after the end of Python 3.7's lifecycle on June 27th, 2023".format(core_constant.NAME))
		print_stderr('Current Python version: {}'.format(platform.python_version()))


def entry_point():
	environment_check()

	from mcdreforged.cli.cmd_gendefault import generate_default_stuffs
	from mcdreforged.cli.cmd_init import initialize_environment
	from mcdreforged.cli.cmd_pack import make_packed_plugin
	from mcdreforged.cli.cmd_run import run_mcdr
	from mcdreforged.cli.cmd_version import show_version

	if len(sys.argv) == 1:
		run_mcdr()
		return

	parser = ArgumentParser(
		prog=core_constant.PACKAGE_NAME,
		description='{} CLI'.format(core_constant.NAME),
	)
	parser.add_argument('-q', '--quiet', help='Disable CLI output', action='store_true')
	parser.add_argument('-V', '--version', help='Print {} version and exit'.format(core_constant.NAME), action='store_true')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='subparser_name')

	subparsers.add_parser('start', help='Start {}'.format(core_constant.NAME))
	subparsers.add_parser('init', help='Prepare the working environment of {}. Create commonly used folders and generate default configuration and permission files'.format(core_constant.NAME))
	subparsers.add_parser('gendefault', help='Generate default configuration and permission files at current working directory. Existed files will be overwritten')

	parser_pack = subparsers.add_parser('pack', help='Pack plugin files into a packed plugin')
	parser_pack.add_argument('-i', '--input', help='The input directory which the plugin is in. Default: current directory', default='.')
	parser_pack.add_argument('-o', '--output', help='The output directory to store the zipped plugin. Default: current directory', default='.')
	parser_pack.add_argument('-n', '--name', help='A specific name to the output zipped plugin file. If not given the metadata specific name or a default one will be used', default=None)
	parser_pack.add_argument('--ignore-patterns', nargs='+', metavar='IGNORE_PATTERN', help='A list of gitignore-like pattern, indicating a set of files and directories to be ignored during plugin packing. Overwrites values from --ignore-file', default=[])
	parser_pack.add_argument('--ignore-file', help="The path to a utf8-encoded gitignore-like file. It's content will be used as the --ignore-patterns parameter. Default: .gitignore", default='.gitignore')
	parser_pack.add_argument('--shebang', help='Add a "#!"-prefixed shebang line at the beginning of the packed plugin. It will also make the packed plugin executable on POSIX. By default no shebang line will be added. Example: --shebang "/usr/bin/env python3"')

	args = parser.parse_args()

	if args.version:
		show_version(quiet=args.quiet)
		return

	if args.subparser_name == 'start':
		run_mcdr()
	elif args.subparser_name == 'init':
		initialize_environment(quiet=args.quiet)
	elif args.subparser_name == 'gendefault':
		generate_default_stuffs(quiet=args.quiet)
	elif args.subparser_name == 'pack':
		make_packed_plugin(args, quiet=args.quiet)
