"""
Info and InfoSource
"""
import dataclasses
import threading
from enum import Enum
from typing import TYPE_CHECKING, Optional

from mcdreforged.command.command_source import ConsoleCommandSource, PlayerCommandSource, InfoCommandSource
from mcdreforged.utils.exception import IllegalStateError, IllegalCallError

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.si.server_interface import ServerInterface


class InfoSource(int, Enum):
	"""
	Sources where an :class:`Info` object comes from
	"""

	SERVER = 0
	"""From the standard output stream of the server"""

	CONSOLE = 1
	"""From input from console"""


class _InfoIdCounter:
	lock = threading.Lock()
	counter = 0

	@classmethod
	def acquire(cls) -> int:
		with cls.lock:
			ret = cls.counter
			cls.counter += 1
		return ret


@dataclasses.dataclass
class _InfoControlData:
	mcdr_server: 'MCDReforgedServer'
	command_source: InfoCommandSource
	should_send_to_server: bool


@dataclasses.dataclass
class Info:
	"""
	An :class:`Info` instance contains the parsed result from the server or from the console
	"""

	source: InfoSource
	"""
	A int (actually :class:`InfoSource`, a subclass of int) representing the the type of the info

	For info from the server, its value is ``0``

	For info from the console, its value is ``1``

	See :class:`InfoSource` for all possible values
	"""

	raw_content: str
	"""
	Very raw unparsed content from the server stdout.

	It's also the content to be echoed to the stdout
	"""

	id: int = dataclasses.field(default_factory=_InfoIdCounter.acquire)
	"""A monotonously increasing unique id"""

	hour: Optional[int] = None
	"""Time information from the parsed text - hour"""
	min: Optional[int] = None
	"""Time information from the parsed text - minute"""
	sec: Optional[int] = None
	"""Time information from the parsed text - second"""

	content: Optional[str] = None
	"""
	The parsed message text

	If the text is sent by a player it will be what the player said.
	Otherwise it will be the content that removes stuffs like timestamp or thread name
	"""

	player: Optional[str] = None
	"""
	The name of the player

	If it's not sent by a player the value will be None
	"""

	logging_level: Optional[str] = None
	"""The logging level of the server's stdout, such as ``"INFO"`` or ``"WARN"``"""

	@property
	def is_from_console(self) -> bool:
		"""
		If the source of the info is :attr:`InfoSource.CONSOLE` (``1``), i.e. from the console
		"""
		return self.source == InfoSource.CONSOLE

	@property
	def is_from_server(self) -> bool:
		"""
		If the source of the info is :attr:`InfoSource.SERVER` (``0``), i.e. from the server
		"""
		return self.source == InfoSource.SERVER

	@property
	def is_player(self) -> bool:
		"""
		If the source is from a player in the server
		"""
		return self.is_from_server and self.player is not None

	@property
	def is_user(self) -> bool:
		"""
		If the source is from a user, i.e. if the source is from the console or from a player in the server
		"""
		return self.is_from_console or self.is_player

	def get_server(self) -> 'ServerInterface':
		"""
		Return the server interface instance
		"""
		return self.__icd.mcdr_server.basic_server_interface

	def get_command_source(self) -> Optional[InfoCommandSource]:
		"""
		Extract a command source object from this object:

		* :class:`~mcdreforged.command.command_source.ConsoleCommandSource` if this info is from console
		* :class:`~mcdreforged.command.command_source.PlayerCommandSource` if this info is from a player in the server

		:return: The command source instance, or None if it can't extract a command source
		"""
		return self.__icd.command_source

	def to_command_source(self) -> InfoCommandSource:
		"""
		The same to method :meth:`get_command_source`,
		but it raises a :class:`~mcdreforged.utils.exception.IllegalCallError` if it can't extract a command source

		:raise IllegalCallError: if a command source cannot be extracted from this object
		"""
		source = self.get_command_source()
		if source is None:
			raise IllegalCallError()
		return source

	def should_send_to_server(self) -> bool:
		"""
		Representing if MCDR should send the content to the standard input stream of the server
		if this info is input from the console
		"""
		return self.__icd.should_send_to_server if self.__control_data else True

	def cancel_send_to_server(self) -> None:
		"""
		Prevent this info from being sent to the standard input stream of the server
		"""
		self.__icd.should_send_to_server = False

	# -----------------------
	#      Non-API Below
	# -----------------------

	__control_data: Optional[_InfoControlData] = dataclasses.field(default=None, repr=False, compare=False)

	@property
	def __icd(self) -> _InfoControlData:
		if self.__control_data is None:
			raise IllegalStateError('This info instance has not been finalized, the API you called is not available yet')
		return self.__control_data

	def _attach_and_finalize(self, mcdr_server: 'MCDReforgedServer'):
		"""
		**Not public API**
		"""
		def create_command_source() -> Optional[InfoCommandSource]:
			if self.is_from_console:
				return ConsoleCommandSource(mcdr_server, self)
			elif self.is_player:
				return PlayerCommandSource(mcdr_server, self, self.player)
			return None

		self.__control_data = _InfoControlData(
			mcdr_server=mcdr_server,
			command_source=create_command_source(),
			should_send_to_server=True,
		)