from abc import ABC, abstractmethod
from typing import Optional, Tuple

from typing_extensions import deprecated

from mcdreforged.handler.handler_spec import StopMethod, StopMethods
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types.message import MessageText


class ServerHandler(ABC):
	"""
	The interface class for server handler

	Class inheriting tree::

		ServerHandler (interface)
		├── BasicHandler
		└── SpecServerHandler
			└── BuiltinSpecServerHandler
				├── VanillaHandler
				├── Beta18Handler
				├── ForgeHandler
				├── BukkitHandler
				├── Bukkit14Handler
				├── CatServerHandler
				├── ArclightHandler
				├── BungeecordHandler
				├── WaterfallHandler
				└── VelocityHandler
	"""

	def __new__(cls, *args, **kwargs):
		if cls.get_stop_method is ServerHandler.get_stop_method and cls.get_stop_command is ServerHandler.get_stop_command:
			raise TypeError("Can't instantiate handler class {} without an implementation for get_stop_method or get_stop_command".format(cls.__name__))
		return super().__new__(cls)

	# ---------------------
	#   Basic Information
	# ---------------------

	@abstractmethod
	def get_name(self) -> str:
		"""
		The name of the server handler

		The name is used as the identifier of this server handler in MCDR configuration
		"""
		...

	# ------------------
	#   Server control
	# ------------------

	@deprecated('Use get_stop_method instead', category=None)
	def get_stop_command(self) -> str:
		"""
		The command to stop the server

		The default implementation derives the command from :meth:`get_stop_method`

		.. deprecated:: v2.17.0
			Use :meth:`get_stop_method` instead
		"""
		if type(self).get_stop_method is ServerHandler.get_stop_method:
			raise NotImplementedError('handler {!r} implements neither get_stop_method nor get_stop_command'.format(self.get_name()))
		stop = self.get_stop_method()
		if not isinstance(stop, StopMethods.Command):
			raise ValueError('handler {!r} does not stop the server with a command'.format(self.get_name()))
		return stop.command

	def get_stop_method(self) -> StopMethod:
		"""
		The method to stop the server

		At least one of this method and :meth:`get_stop_command` must be implemented, or the handler class cannot be instantiated.
		The default implementation wraps the result of :meth:`get_stop_command`

		.. versionadded:: v2.17.0
		"""
		if type(self).get_stop_command is ServerHandler.get_stop_command:
			raise NotImplementedError('handler {!r} implements neither get_stop_method nor get_stop_command'.format(self.get_name()))
		return StopMethods.Command(command=self.get_stop_command())

	@abstractmethod
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		"""
		The command to send a message to a target
		"""
		...

	@abstractmethod
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		"""
		The command to broadcast a message in the server
		"""
		...

	# -------------------------
	#   Server output parsing
	# -------------------------

	@abstractmethod
	def pre_parse_server_stdout(self, text: str) -> str:
		"""
		A parsing preprocessor. Invoked before any parsing operation

		Remove useless / annoying things like control characters in the text before parsing

		:param text: A line of the server stdout to be parsed
		"""
		...

	@abstractmethod
	def parse_console_command(self, text: str) -> Info:
		"""
		Parse console input

		:param text: A line of console input to be parsed
		:return: An :class:`~mcdreforged.info_reactor.info.Info` object as the result
		"""
		...

	@abstractmethod
	def parse_server_stdout(self, text: str) -> Info:
		"""
		Main parsing operation. Parse a string from the stdout of the server and output a parsed info

		It may raise any exceptions if the format of the input string is not correct

		:param text: A line of the server stdout to be parsed, processed by :meth:`pre_parse_server_stdout`
		:return: An :class:`~mcdreforged.info_reactor.info.Info` object as the result
		"""
		...

	@abstractmethod
	def parse_player_joined(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicating a player joined message

		If it is, returns the name of the player, otherwise returns None

		:param info: The info object to be checked
		:return: The name of the player, or None
		"""
		...

	@abstractmethod
	def parse_player_left(self, info: Info) -> Optional[str]:
		"""
		Check if the info indicates a player left message

		If it is, returns the name of the player, otherwise returns None

		:param info: The info object to be checked
		:return: The name of the player, or None
		"""
		...

	@abstractmethod
	def parse_server_version(self, info: Info) -> Optional[str]:
		"""
		Check if the info contains a server version message

		If it is, returns server version, otherwise returns None

		:param info: The info object to be checked
		:return: The version of the server, or None
		"""
		...

	@abstractmethod
	def parse_server_address(self, info: Info) -> Optional[Tuple[str, int]]:
		"""
		Check if the info contains the address which the server is listening on

		If it is, returns server ip and port it's listening on, otherwise returns None

		:param info: The info object to be checked
		:return: A tuple containing the ip and the port, or None
		"""
		...

	@abstractmethod
	def test_server_startup_done(self, info: Info) -> bool:
		"""
		Check if the info indicates a server startup message

		:param info: The info object to be checked
		:return: If the info indicates a server startup message
		"""
		...

	@abstractmethod
	def test_rcon_started(self, info: Info) -> bool:
		"""
		Check if rcon has started

		:param info: The info object to be checked
		:return: If rcon has started
		"""
		...

	@abstractmethod
	def test_server_stopping(self, info: Info) -> bool:
		"""
		Check if the server is stopping

		:param info: The info object to be checked
		:return: If the server is stopping
		"""
		...

	@abstractmethod
	def validate_player_name(self, name: str) -> bool:
		"""
		Check if the given player name is valid

		:param name: The name to be validated
		:return: True if the name is a valid player name, otherwise False

		.. versionadded:: v2.16.0
		"""
		...
