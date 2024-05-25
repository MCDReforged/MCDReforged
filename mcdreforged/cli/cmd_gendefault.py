import os

from mcdreforged.mcdr_server import MCDReforgedServer
from mcdreforged.mcdr_server_args import MCDReforgedServerArgs


def generate_default_stuffs(*, config_file_path: str, permission_file_path: str, quiet: bool = False):
	MCDReforgedServer(MCDReforgedServerArgs(
		generate_default_only=True,
		config_file_path=config_file_path,
		permission_file_path=permission_file_path,
	))
	if not quiet:
		print('Generated default configuration and permission files in {}'.format(os.getcwd()))
