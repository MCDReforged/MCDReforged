import platform
import sys

__all__ = ['entrypoint']


def __environment_check():
	"""
	This should even work in python 2.7+
	"""
	# only mcdreforged.constants is allowed to load before the boostrap() call
	from mcdreforged.constants import core_constant

	if sys.version_info < (3, 8):
		print('Python 3.8+ is needed to run {}'.format(core_constant.NAME))
		print('Current Python version {} is too old'.format(platform.python_version()))
		sys.exit(1)


def entrypoint():
	"""
	The one and only entrypoint for MCDR

	All MCDR launches start from here
	"""
	__environment_check()

	from mcdreforged.mcdr_boostrap import boostrap
	boostrap()

	from mcdreforged.cli import cli_entry
	cli_entry.cli_dispatch()
