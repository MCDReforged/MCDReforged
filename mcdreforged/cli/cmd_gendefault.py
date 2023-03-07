import os

from mcdreforged.mcdr_server import MCDReforgedServer


def generate_default_stuffs(*, quiet: bool = False):
	MCDReforgedServer(generate_default_only=True)
	if not quiet:
		print('Generated default configuration and permission files in {}'.format(os.getcwd()))
