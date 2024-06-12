"""
Info and InfoSource
"""
from enum import Enum
from typing import TYPE_CHECKING, Optional

from mcdreforged.command.command_source import ConsoleCommandSource, PlayerCommandSource, \
	InfoCommandSource
from mcdreforged.utils import class_utils
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


class Info:
	"""
	An :class:`Info` instance contains the parsed result from the server or from the console
	"""
	__id_counter = 0

	def __init__(self, source: InfoSource, raw_content: str):
		self.id: int = Info.__id_counter
		"""A monotonously increasing unique id"""

		Info.__id_counter += 1
		self.__mcdr_server: Optional['MCDReforgedServer'] = None
		self.__send_to_server = True
		self.__command_source = None

		# -----------------
		#   Public fields
		# -----------------

		self.hour: Optional[int] = None
		"""Time information from the parsed text - hour"""
		self.min: Optional[int] = None
		"""Time information from the parsed text - minute"""
		self.sec: Optional[int] = None
		"""Time information from the parsed text - second"""

		self.raw_content: str = raw_content
		"""
		Very raw unparsed content from the server stdout.

		It's also the content to be echoed to the stdout
		"""

		self.content: Optional[str] = None
		"""
		The parsed message text
		
		If the text is sent by a player it will be what the player said.
		Otherwise it will be the content that removes stuffs like timestamp or thread name
		"""

		self.__player: Optional[str] = None  # See the player property

		self.source: InfoSource = source
		"""
		A int (actually :class:`InfoSource`, a subclass of int) representing the the type of the info

		For info from the server, its value is ``0``
		
		For info from the console, its value is ``1``
		
		See :class:`InfoSource` for all possible values
		"""

		self.logging_level: Optional[str] = None
		"""The logging level of the server's stdout, such as ``"INFO"`` or ``"WARN"``"""

		# -----------------
		#      Caches
		# -----------------
		self.__is_user: bool = False
		self.__update_cache()

	def __update_cache(self):
		self.__is_user = self.is_from_console or self.is_player

	@property
	def player(self) -> Optional[str]:
		"""
		The name of the player

		If it's not sent by a player the value will be None
		"""
		return self.__player

	@player.setter
	def player(self, player: str):
		self.__player = player
		self.__update_cache()

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
		return self.__is_user

	# --------------
	#      API
	# --------------

	def __assert_attached(self):
		if self.__mcdr_server is None:
			raise IllegalStateError('MCDR server is not attached to this Info instance yet')

	def attach_mcdr_server(self, mcdr_server: 'MCDReforgedServer'):
		"""
		**Not public API**

		:meta private:
		"""
		if self.__mcdr_server is not None and self.__mcdr_server is not mcdr_server:
			raise IllegalStateError('An Info instance can only attach one MCDR server')
		self.__mcdr_server = mcdr_server

	def get_server(self) -> 'ServerInterface':
		"""
		Return the server interface instance
		"""
		return self.__mcdr_server.basic_server_interface

	def get_command_source(self) -> Optional[InfoCommandSource]:
		"""
		Extract a command source object from this object:

		* :class:`~mcdreforged.command.command_source.ConsoleCommandSource` if this info is from console
		* :class:`~mcdreforged.command.command_source.PlayerCommandSource` if this info is from a player in the server

		:return: The command source instance, or None if it can't extract a command source
		"""
		self.__assert_attached()
		if self.__command_source is None:
			if self.is_from_console:
				self.__command_source = ConsoleCommandSource(self.__mcdr_server, self)
			elif self.is_player:
				self.__command_source = PlayerCommandSource(self.__mcdr_server, self, self.player)
		return self.__command_source

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
		return self.__send_to_server

	def cancel_send_to_server(self) -> None:
		"""
		Prevent this info from being sent to the standard input stream of the server
		"""
		self.__send_to_server = False

	# --------------------------------
	#   Formatting and Magic methods
	# --------------------------------

	def __repr__(self):
		return class_utils.represent(self)

	def __deepcopy__(self, memo: dict):
		"""
		Just don't copy the mcdr_server instance
		"""
		existed = memo.get(self)
		if existed is not None:
			return existed
		memo[self] = dupe = Info(self.source, self.raw_content)
		dupe.hour, dupe.min, dupe.sec = self.hour, self.min, self.sec
		dupe.content = self.content
		dupe.player = self.player
		dupe.logging_level = self.logging_level
		return dupe
