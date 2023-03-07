import os

from mcdreforged.constants import core_constant
from mcdreforged.mcdr_server import MCDReforgedServer


def initialize_environment(*, quiet: bool = False):
	MCDReforgedServer(initialize_environment=True)
	if not quiet:
		print('Initialized environment for {} in {}'.format(core_constant.NAME, os.getcwd()))
