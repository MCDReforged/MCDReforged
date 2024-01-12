from argparse import ArgumentParser, Namespace
from typing import Callable

from mcdreforged.cli.pim.plugin_installer import PluginInstaller
from mcdreforged.cli.pim.replier import NoopReplier, StdoutReplier
from mcdreforged.command.command_source import CommandSource


class CliCommandSource(CommandSource):
	pass


# pim list
# pim download <> <> <> <> -o <> <> <>
# pim install <> <> <>
# pim uninstall <> <> <>
def create(parser_factory: Callable[..., ArgumentParser]) -> ArgumentParser:
	parser = parser_factory(name='pim', help='Plugin Installer for MCDReforged')
	subparsers = parser.add_subparsers(title='Command', help='Available commands', dest='pim_command')

	subparsers.add_parser('test', help='Test')
	subparsers.add_parser('list', help='List plugin from the official plugin catalogue')

	parser_download = subparsers.add_parser('download', help='List plugin from the official plugin catalogue')
	parser_download.add_argument('plugin_ids', nargs='+', help='Plugin IDs to be downloaded')
	parser_download.add_argument('-t', '--target', default='.', help='Path to store the downloaded plugins')

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
