import copy
from typing import Optional


class ServerInformation:
	version: Optional[str] = None
	ip: Optional[str] = None
	port: Optional[int] = None

	def clear(self):
		self.version, self.ip, self.port = None, None, None

	def copy(self) -> 'ServerInformation':
		return copy.copy(self)

