import sys
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from typing import cast

from mcdreforged.cli import cmd_pim
from mcdreforged.cli.cmd_gendefault import generate_default_stuffs
from mcdreforged.cli.cmd_init import initialize_environment
from mcdreforged.cli.cmd_pack import make_packed_plugin, PackArgs
from mcdreforged.cli.cmd_reformat_config import reformat_config
from mcdreforged.cli.cmd_run import run_mcdr
from mcdreforged.cli.cmd_version import show_version
from mcdreforged.constants import core_constant
from mcdreforged.mcdr_server_args import MCDReforgedServerArgs


def cli_dispatch():
	if len(sys.argv) == 1:
		run_mcdr(MCDReforgedServerArgs())
		return

	parser = ArgumentParser(
		prog=core_constant.CLI_COMMAND,
		description='{} CLI'.format(core_constant.NAME),
		formatter_class=ArgumentDefaultsHelpFormatter,
	)
	parser.add_argument('-q', '--quiet', help='Disable CLI output', action='store_true')
	parser.add_argument('-V', '--version', help='Print {} version and exit'.format(core_constant.NAME), action='store_true')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='command')

	def add_config_permission_path_args(p: ArgumentParser):
		p.add_argument('--config', metavar='CONFIG_FILE', help='Path to the MCDReforged configuration file', default=core_constant.CONFIG_FILE_PATH)
		p.add_argument('--permission', metavar='PERMISSION_FILE', help='Path to the MCDReforged permission file', default=core_constant.PERMISSION_FILE_PATH)

	parser_gendefault = subparsers.add_parser('gen-default', aliases=['gendefault'], help='Generate default configuration and permission files at current working directory. Existing files will be overwritten', formatter_class=ArgumentDefaultsHelpFormatter)
	add_config_permission_path_args(parser_gendefault)

	parser_init = subparsers.add_parser('init', help='Prepare the working environment of {}. Create commonly used folders and generate default configuration and permission files'.format(core_constant.NAME), formatter_class=ArgumentDefaultsHelpFormatter)
	add_config_permission_path_args(parser_init)

	parser_pack = subparsers.add_parser('pack', help='Pack plugin files into a packed plugin', formatter_class=ArgumentDefaultsHelpFormatter)
	parser_pack.add_argument('-i', '--input', help='The input directory which the plugin is in', default='.')
	parser_pack.add_argument('-o', '--output', help='The output directory to store the zipped plugin', default='.')
	parser_pack.add_argument('-n', '--name', help='A specific name to the output zipped plugin file. If not given the metadata specific name or a default one will be used', default=None)
	parser_pack.add_argument('--ignore-patterns', nargs='+', metavar='IGNORE_PATTERN', help='A list of gitignore-like pattern, indicating a set of files and directories to be ignored during plugin packing. Overwrites values from --ignore-file', default=[])
	parser_pack.add_argument('--ignore-file', help='The path to a utf8-encoded gitignore-like file. It\'s content will be used as the --ignore-patterns parameter', default='.gitignore')
	parser_pack.add_argument('--shebang', help='Add a "#!"-prefixed shebang line at the beginning of the packed plugin. It will also make the packed plugin executable on POSIX. By default no shebang line will be added. Example: --shebang "/usr/bin/env python3"')

	parser_pim = cmd_pim.create(subparsers.add_parser)

	parser_rc = subparsers.add_parser('reformat-config', help='Reformat the MCDReforged configuration file', formatter_class=ArgumentDefaultsHelpFormatter)
	parser_rc.add_argument('-i', '--input', required=True, help='The configuration file of MCDReforged to be reformatted')
	parser_rc.add_argument('-o', '--output', help='Path to the reformatted configuration file. If not provided, output to the input file')

	parser_start = subparsers.add_parser('start', help='Start {}'.format(core_constant.NAME), formatter_class=ArgumentDefaultsHelpFormatter)
	parser_start.add_argument('--auto-init', action='store_true', help='Automatically initialize the working environment if needed')
	parser_start.add_argument('--no-server-start', action='store_true', help='Do not start the server on MCDR startup')
	add_config_permission_path_args(parser_start)

	args = parser.parse_args()

	if args.version:
		show_version(quiet=args.quiet)
		return

	elif args.command == 'gendefault':
		generate_default_stuffs(
			config_file_path=args.config,
			permission_file_path=args.permission,
			quiet=args.quiet,
		)
	elif args.command == 'init':
		initialize_environment(
			config_file_path=args.config,
			permission_file_path=args.permission,
			quiet=args.quiet,
		)
	elif args.command == 'pack':
		make_packed_plugin(cast(PackArgs, args), quiet=args.quiet)
	elif args.command == 'pim':
		cmd_pim.entry(parser_pim, args)
	elif args.command == 'reformat-config':
		reformat_config(args.input, args.output)
	elif args.command == 'start':
		run_mcdr(MCDReforgedServerArgs(
			auto_init=args.auto_init,
			no_server_start=args.no_server_start,
			config_file_path=args.config,
			permission_file_path=args.permission,
		))
