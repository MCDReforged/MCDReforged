from argparse import ArgumentParser, Namespace
from typing import Callable

from mcdreforged.plugin.installer.plugin_installer import PluginInstaller
from mcdreforged.plugin.installer.replier import NoopReplier, StdoutReplier
from mcdreforged.command.command_source import CommandSource


class CliCommandSource(CommandSource):
	pass


# pim list
# pim download <id> -o <file_name>
# pim install <> <> <>
# pim uninstall <> <> <>
# pim freeze
def create(parser_factory: Callable[..., ArgumentParser]) -> ArgumentParser:
	parser = parser_factory(name='pim', help='Plugin Installer for MCDReforged')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='pim_command')

	subparsers.add_parser('test', help='Test')
	subparsers.add_parser('list', help='List plugin from the official plugin catalogue')

	parser_download = subparsers.add_parser('download', help='Download given plugins. No dependency resolution will be made')
	parser_download.add_argument('plugin_ids', nargs='+', help='Plugin IDs to be downloaded')
	parser_download.add_argument('-o', '--output', default='.', help='Path to store the downloaded plugins')

	parser_download = subparsers.add_parser('install', help='Install given plugins and its dependencies')
	parser_download.add_argument('plugin_ids', nargs='+', help='Plugin IDs to be downloaded')
	parser_download.add_argument('-o', '--output', default='.', help='Path to store the downloaded plugins')

	return parser


def entry(parser: ArgumentParser, args: Namespace):
	cmd = args.pim_command

	if cmd is None:
		parser.print_help()

	# TODO: make use of return value
	installer = PluginInstaller(NoopReplier() if args.quiet else StdoutReplier())
	if cmd == 'test':
		installer.test_stuffs()
	if cmd == 'list':
		installer.list_plugin()
	elif cmd == 'download':
		installer.download_plugin(args.plugin_ids, args.target)
