from abc import ABC, abstractmethod
from typing import Optional, Tuple

from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types.message import MessageText


class ServerHandler(ABC):
	"""
	The interface class for server handler

	Class inheriting tree::

		ServerHandler (interface)
		├── BasicHandler
		└── AbstractServerHandler
			├── AbstractMinecraftHandler
			│   ├── VanillaHandler
			│   ├── Beta18Handler
			│   ├── ForgeHandler
			│   └── BukkitHandler
			│       ├── Bukkit14Handler
			│       ├── CatServerHandler
			│       └── ArclightHandler
			├── BungeecordHandler
			│   └── WaterfallHandler
			└── VelocityHandler
	"""

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

	@abstractmethod
	def get_stop_command(self) -> str:
		"""
		The command to stop the server
		"""
		...

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

		In this default implementation, it firstly uses :meth:`_get_server_stdout_raw_result`
		to get a raw :class:`~mcdreforged.info_reactor.info.Info` object,
		then use :meth:`_content_parse` to fill generic information into the :class:`~mcdreforged.info_reactor.info.Info` object,
		finally returns that as a simply-parsed info

		If the server handler is able to parse more information, you can do more post-parsing operations after invoking this method via ``super()``

		:param text: A line of the server stdout to be parsed
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
