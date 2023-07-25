import io
import sys
import warnings


def boostrap():
	"""
	Do some boostrap things before non-std modules get loaded
	"""

	# 1. Ensure line_buffering is True for stdout / stderr
	# Prevent stdout / stderr goes into block-buffered mode, if the stdio of MCDR is wrapped by other programs
	# See issue #257

	# stderr might be fully buffered before python 3.9, so reconfigure it as well
	for name, stream in {'sys.stdout': sys.stdout, 'sys.stderr': sys.stderr}.items():
		if isinstance(stream, io.TextIOWrapper):
			stream.reconfigure(line_buffering=True)
		else:
			warnings.warn('{} {} is not a io.TextIOWrapper, cannot apply reconfigure'.format(name, stream))
