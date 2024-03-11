from argparse import ArgumentParser, Namespace
from typing import Callable

from typing_extensions import NoReturn

import sys
from mcdreforged.plugin.installer.plugin_installer import PluginInstaller
from mcdreforged.plugin.installer.replier import NoopReplier, StdoutReplier


# pim list
# pim download <id> -o <file_name>
# pim install <> <> <>
# pim uninstall <> <> <>
# pim freeze
def create(parser_factory: Callable[..., ArgumentParser]) -> ArgumentParser:
	parser = parser_factory(name='pim', help='Plugin Installer for MCDReforged')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='pim_command')

	subparsers.add_parser('test', help='test command')

	parser_list = subparsers.add_parser('list', help='List plugin from the official plugin catalogue')
	parser_list.add_argument('search', nargs='?', default=None, help='Search keyword to filter the plugins')

	parser_download = subparsers.add_parser('download', help='Download given plugins. No dependency resolution will be made')
	parser_download.add_argument('plugin_ids', nargs='+', help='Plugin IDs to be downloaded')
	parser_download.add_argument('-o', '--output', default='.', help='Path to store the downloaded plugins')
	parser_download.add_argument('-d', '--dependencies', action='store_true', help='if dependencies of the given plugins should also be downloaded')

	return parser


def __entry(parser: ArgumentParser, args: Namespace) -> int:
	cmd = args.pim_command

	if cmd is None:
		parser.print_help()
		return 1

	replier = NoopReplier() if args.quiet else StdoutReplier()
	installer = PluginInstaller(replier)

	if cmd == 'test':
		return installer.test_stuffs()
	elif cmd == 'list':
		return installer.list_plugin(keyword=args.search)
	elif cmd == 'download':
		return installer.download_plugin(args.plugin_ids, args.output)
	else:
		print('unknown cmd {!r}'.format(cmd))
		return 1


def entry(parser: ArgumentParser, args: Namespace) -> NoReturn:
	sys.exit(__entry(parser, args))
