import io
import os
import sys
import warnings
from pathlib import Path


__all__ = ['boostrap']


def boostrap():
	"""
	Do some boostrap things before non-std modules get loaded
	"""
	__disable_stdout_stderr_block_buffering()
	__ensure_cwd_is_in_sys_path()


def __disable_stdout_stderr_block_buffering():
	"""
	Ensure line_buffering is True for stdout / stderr

	Prevent stdout / stderr goes into block-buffered mode, if the stdio of MCDR is wrapped by other programs
	See issue #257

	stderr might be fully buffered before python 3.9, so reconfigure it as well
	"""
	for name, stream in {'sys.stdout': sys.stdout, 'sys.stderr': sys.stderr}.items():
		if isinstance(stream, io.TextIOWrapper):
			stream.reconfigure(line_buffering=True)
		else:
			warnings.warn(f'{name!r} {stream!r} is not a io.TextIOWrapper, cannot invoke reconfigure')


def __ensure_cwd_is_in_sys_path():
	"""
	Make sure current directory is in the ``sys.path``, so custom handlers / reactors can be properly imported

	Ensure the module search behavior consistency between different launch methods, e.g. between

	- ``python -m mcdreforged``, sys.path[0] will be the current working directory
	- ``mcdreforged``, sys.path[0] will be the binary file (it's a valid pyz file)

	Reference: https://docs.python.org/3/library/sys.html#sys.path

	See issue #277, #331
	"""

	cwd = os.getcwd()
	try:
		if len(sys.path) > 0:
			path0 = Path(sys.path[0])
			ok = path0.is_dir() and path0.samefile(cwd)
		else:
			ok = False
		if not ok:
			sys.path.insert(0, cwd)
	except OSError as e:
		warnings.warn(f'Fail to check and insert cwd {cwd!r} into sys.path {sys.path}: {e}')
