import platform
import sys

# only mcdreforged.constants is allowed to load before the boostrap() call
from mcdreforged.constants import core_constant
from mcdreforged.mcdr_boostrap import boostrap


def environment_check():
	"""
	This should even work in python 2.7+
	"""
	python_version = sys.version_info.major + sys.version_info.minor * 0.1
	if python_version < 3.8:
		print('Python 3.8+ is needed to run {}'.format(core_constant.NAME))
		print('Current Python version {} is too old'.format(platform.python_version()))
		sys.exit(1)


def entrypoint():
	"""
	The one and only entrypoint for MCDR

	All MCDR launches start from here
	"""
	boostrap()
	environment_check()

	from mcdreforged.cli import cli_entry
	cli_entry.cli_dispatch()
