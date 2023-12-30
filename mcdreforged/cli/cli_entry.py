import sys
from argparse import ArgumentParser

from mcdreforged.cli.cmd_gendefault import generate_default_stuffs
from mcdreforged.cli.cmd_init import initialize_environment
from mcdreforged.cli.cmd_pack import make_packed_plugin
from mcdreforged.cli.cmd_pip_install import pip_install_from_plugins
from mcdreforged.cli.cmd_run import run_mcdr
from mcdreforged.cli.cmd_version import show_version
from mcdreforged.constants import core_constant


def cli_dispatch():
	if len(sys.argv) == 1:
		run_mcdr(auto_init=False)
		return

	parser = ArgumentParser(
		prog=core_constant.CLI_COMMAND,
		description='{} CLI'.format(core_constant.NAME),
	)
	parser.add_argument('-q', '--quiet', help='Disable CLI output', action='store_true')
	parser.add_argument('-V', '--version', help='Print {} version and exit'.format(core_constant.NAME), action='store_true')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='command')

	subparsers.add_parser('gendefault', help='Generate default configuration and permission files at current working directory. Existed files will be overwritten')
	subparsers.add_parser('init', help='Prepare the working environment of {}. Create commonly used folders and generate default configuration and permission files'.format(core_constant.NAME))

	parser_pack = subparsers.add_parser('pack', help='Pack plugin files into a packed plugin')
	parser_pack.add_argument('-i', '--input', help='The input directory which the plugin is in. Default: current directory', default='.')
	parser_pack.add_argument('-o', '--output', help='The output directory to store the zipped plugin. Default: current directory', default='.')
	parser_pack.add_argument('-n', '--name', help='A specific name to the output zipped plugin file. If not given the metadata specific name or a default one will be used', default=None)
	parser_pack.add_argument('--ignore-patterns', nargs='+', metavar='IGNORE_PATTERN', help='A list of gitignore-like pattern, indicating a set of files and directories to be ignored during plugin packing. Overwrites values from --ignore-file', default=[])
	parser_pack.add_argument('--ignore-file', help="The path to a utf8-encoded gitignore-like file. It's content will be used as the --ignore-patterns parameter. Default: .gitignore", default='.gitignore')
	parser_pack.add_argument('--shebang', help='Add a "#!"-prefixed shebang line at the beginning of the packed plugin. It will also make the packed plugin executable on POSIX. By default no shebang line will be added. Example: --shebang "/usr/bin/env python3"')

	parser_pipi = subparsers.add_parser('pipi', help='Call "pip install" with the requirements.txt file in the given packed plugin to install Python packages')
	parser_pipi.add_argument('plugin_paths', nargs='*', help='The packed plugin files to be processed')
	parser_pipi.add_argument('--args', help='Extra arguments passing to the pip process, e.g. --args "--proxy http://localhost:8080"')

	parser_start = subparsers.add_parser('start', help='Start {}'.format(core_constant.NAME))
	parser_start.add_argument('--auto-init', action='store_true', help='Automatically initialize the working environment if needed')

	args = parser.parse_args()

	if args.version:
		show_version(quiet=args.quiet)
		return

	elif args.command == 'gendefault':
		generate_default_stuffs(quiet=args.quiet)
	elif args.command == 'init':
		initialize_environment(quiet=args.quiet)
	elif args.command == 'pack':
		make_packed_plugin(args, quiet=args.quiet)
	elif args.command == 'pipi':
		pip_install_from_plugins(args.plugin_paths, extra_args=args.args, quiet=args.quiet)
	elif args.command == 'start':
		run_mcdr(auto_init=args.auto_init)
