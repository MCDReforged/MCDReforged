import copy
from typing import Optional


class ServerInformation:
	"""
	Information of the current server, interred from the output of the server

	.. versionadded:: v2.1.0
	"""

	version: Optional[str] = None
	"""Server version name, e.g. ``"1.15.2"``, ``"1.17 Release Candidate 1"``"""

	ip: Optional[str] = None
	"""
	Server IP address, e.g. ``"127.0.0.1"``
	
	Notes that this is the address that the server is listening on, not the physical server's ip address
	"""

	port: Optional[int] = None
	"""Server port, e.g. ``25565``"""

	def clear(self):
		self.version, self.ip, self.port = None, None, None

	def copy(self) -> 'ServerInformation':
		return copy.copy(self)

