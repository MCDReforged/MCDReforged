"""
Info and InfoSource
"""
import dataclasses
import enum
import threading
from typing import TYPE_CHECKING, Optional

from typing_extensions import Self

from mcdreforged.command.command_source import ConsoleCommandSource, PlayerCommandSource, InfoCommandSource
from mcdreforged.utils.exception import IllegalStateError, IllegalCallError

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.si.server_interface import ServerInterface


class InfoSource(int, enum.Enum):
	"""
	Sources where an :class:`Info` object comes from
	"""

	SERVER = 0
	"""From the standard output / standard error stream of the server"""

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


class InfoActionFlag(enum.Flag):
	"""
	A flag variable controlling what actions MCDR will do next with this Info object
	"""

	send_to_server = enum.auto()
	"""
	Send the content from console stdin to server stdin
	"""

	echo_to_console = enum.auto()
	"""
	Print the server output to the console stdout
	"""

	process = enum.auto()
	"""
	Allow subsequent info reactor processing, such as plugin event dispatching
	"""

	@classmethod
	def default(cls) -> Self:
		"""
		The default flag set that allows all actions to be performed
		"""
		return cls.send_to_server | cls.echo_to_console | cls.process

	@classmethod
	def hidden(cls) -> Self:
		"""
		Do not echo the server output to the console, perform the subsequent actions silently
		"""
		return cls.send_to_server | cls.process

	@classmethod
	def discarded(cls) -> Self:
		"""
		Discard the info object right now, no more future processing
		"""
		return cls(0)


_default_info_action_flag = InfoActionFlag.default()


@dataclasses.dataclass
class _InfoControlData:
	mcdr_server: 'MCDReforgedServer'
	command_source: InfoCommandSource


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
	Very raw unparsed content from the server stdout / stderr

	It's also the content to be echoed to the console stdout
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
	"""The logging level of the server's output, such as ``"INFO"`` or ``"WARN"``"""

	action_flag: InfoActionFlag = dataclasses.field(default=_default_info_action_flag)
	"""
	A flag variable controlling what actions MCDR will do next with this Info object

	.. seealso:: class :class:`InfoActionFlag`
	"""

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
		* Otherwise: return None

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
		return InfoActionFlag.send_to_server in self.action_flag

	def cancel_send_to_server(self) -> None:
		"""
		Prevent this info from being sent to the standard input stream of the server
		"""
		self.action_flag &= ~InfoActionFlag.send_to_server

	# -------------------------------
	#      Non-API Section Below
	# -------------------------------

	__control_data: Optional[_InfoControlData] = dataclasses.field(default=None, repr=False, compare=False)

	@property
	def __icd(self) -> _InfoControlData:
		if self.__control_data is None:
			raise IllegalStateError('This info instance has not been finalized, the API you called is not available yet')
		return self.__control_data

	def _attach_and_finalize(self, mcdr_server: 'MCDReforgedServer', *, command_source: Optional[InfoCommandSource] = None):
		"""
		**Not public API**
		"""
		def create_command_source() -> Optional[InfoCommandSource]:
			if command_source is not None:
				return command_source
			if self.is_from_console:
				return ConsoleCommandSource(mcdr_server, self)
			elif self.is_player:
				return PlayerCommandSource(mcdr_server, self, self.player)
			return None

		self.__control_data = _InfoControlData(
			mcdr_server=mcdr_server,
			command_source=create_command_source(),
		)