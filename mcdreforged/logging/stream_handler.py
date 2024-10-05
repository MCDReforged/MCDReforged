import logging
import sys
from threading import Lock
from typing import IO


class _SyncWriteStream:
	"""
	A stream wrapper with its method "write" synchronized.
	All accesses to other attributes are forwarded to the wrapped stream
	"""
	def __init__(self, stream: IO[str]):
		self.sws_stream = stream
		self.sws_lock = Lock()

	def write(self, s: str):
		with self.sws_lock:
			self.sws_stream.write(s)

	def __getattribute__(self, item: str):
		if item in ('write', 'sws_stream', 'sws_lock'):
			return object.__getattribute__(self, item)
		else:
			return self.sws_stream.__getattribute__(item)


class SyncStdoutStreamHandler(logging.StreamHandler):
	__sws = _SyncWriteStream(sys.stdout)

	def __init__(self):
		super().__init__(type(self).__sws)

	@classmethod
	def update_stdout(cls, stream: IO[str]):
		cls.__sws.sws_stream = stream

	@classmethod
	def write_direct(cls, s: str):
		cls.__sws.write(s)
