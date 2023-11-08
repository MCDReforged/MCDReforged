import io
import os
import sys
import warnings


def boostrap():
	"""
	Do some boostrap things before non-std modules get loaded
	"""

	# =============================================================================
	# 1. Ensure line_buffering is True for stdout / stderr
	# Prevent stdout / stderr goes into block-buffered mode, if the stdio of MCDR is wrapped by other programs
	# See issue #257

	# stderr might be fully buffered before python 3.9, so reconfigure it as well
	for name, stream in {'sys.stdout': sys.stdout, 'sys.stderr': sys.stderr}.items():
		if isinstance(stream, io.TextIOWrapper):
			stream.reconfigure(line_buffering=True)
		else:
			warnings.warn('{} {} is not a io.TextIOWrapper, cannot apply reconfigure'.format(name, stream))

	# =============================================================================
	# 2. Make sure current directory is in the sys.path
	# Ensure the module search behavior consistency between different launch methods, e.g. "python -m mcdreforged" and "mcdreforged"
	# Reference: https://docs.python.org/3/library/sys.html#sys.path
	# See issue #277

	cwd = os.getcwd()
	path0 = sys.path[0]
	try:
		if os.path.isdir(cwd) and os.path.isdir(path0) and not os.path.samefile(cwd, path0):
			sys.path.insert(0, cwd)
	except OSError as e:
		warnings.warn('fail to check equality between os.getcwd() {!r} and sys.path[0] {!r}: {}'.format(cwd, path0, e))
