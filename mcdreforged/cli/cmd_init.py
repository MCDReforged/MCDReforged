import os

from mcdreforged.constants import core_constant
from mcdreforged.mcdr_server import MCDReforgedServer
from mcdreforged.mcdr_server_args import MCDReforgedServerArgs


def initialize_environment(*, config_file_path: str, permission_file_path: str, quiet: bool = False):
	MCDReforgedServer(MCDReforgedServerArgs(
		initialize_environment=True,
		config_file_path=config_file_path,
		permission_file_path=permission_file_path,
	))
	if not quiet:
		print('Initialized environment for {} in {}'.format(core_constant.NAME, os.getcwd()))
