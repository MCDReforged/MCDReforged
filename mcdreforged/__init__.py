"""
.. versionadded:: v2.15.0
	Module ``mcdreforged`` now contains everything in ``mcdreforged.api.all``. All MCDR API components can be imported from here
"""


def __python_version_check():
	# This should even work in python 2.7+
	import platform
	import sys
	if sys.version_info < (3, 9):
		raise RuntimeError('MCDReforged requires Python 3.9 or higher to run. Current Python version is {}'.format(platform.python_version()))


__python_version_check()

from mcdreforged.api.all import *

# noinspection PyPep8Naming
from mcdreforged.constants.core_constant import VERSION_PYPI as __version__
