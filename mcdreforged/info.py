"""
Info and InfoSource
"""
from typing import TYPE_CHECKING, Optional

from mcdreforged.command.command_source import ConsoleCommandSource, PlayerCommandSource, \
	InfoCommandSource
from mcdreforged.utils.exception import IllegalStateError, IllegalCallError

if TYPE_CHECKING:
	from mcdreforged.plugin.server_interface import ServerInterface


class InfoSource:
	# the text is from the stdout of the server
	SERVER = 0

	# the text is from user input
	CONSOLE = 1


class Info:
	__id_counter = 0

	def __init__(self):
		# a increasing id number for distinguishing info instance
		self.id = Info.__id_counter
		Info.__id_counter += 1
		# noinspection PyTypeChecker
		self.__mcdr_server = None  # type: 'MCDReforgedServer'
		self.__send_to_server = True
		self.__command_source = None

		# -----------------
		#   Public fields
		# -----------------

		# time information from the parsed text
		self.hour = None  # type: Optional[int]
		self.min = None  # type: Optional[int]
		self.sec = None  # type: Optional[int]

		# very raw content, it's also the content to be echoed to the stdout
		self.raw_content = None  # type: Optional[str]

		# if the text is sent by a player the value will be what the player said. if not the value will be the pain text
		self.content = None  # type: Optional[str]

		# the name of the player. if it's not sent by a player the value will be None
		self.player = None  # type: Optional[str]

		# the value type is InfoSource
		self.source = None  # type: Optional[int]

		# the logging level of the server's stdout, such as "INFO" or "WARN"
		self.logging_level = None  # type: Optional[str]

	@property
	def is_from_console(self):
		return self.source == InfoSource.CONSOLE

	@property
	def is_from_server(self):
		return self.source == InfoSource.SERVER

	@property
	def is_player(self):
		return self.is_from_server and self.player is not None

	@property
	def is_user(self):
		return self.is_from_console or self.is_player

	# --------------
	#      API
	# --------------

	def __assert_attached(self):
		if self.__mcdr_server is None:
			raise IllegalStateError('MCDR server is not attached to this Info instance yet')

	def attach_mcdr_server(self, mcdr_server):
		if self.__mcdr_server is not None:
			raise IllegalStateError('An Info instance can only attach the MCDR server once')
		self.__mcdr_server = mcdr_server

	def get_server(self) -> 'ServerInterface':
		return self.__mcdr_server.server_interface

	def get_command_source(self) -> Optional[InfoCommandSource]:
		self.__assert_attached()
		if self.__command_source is None:
			if self.is_from_console:
				self.__command_source = ConsoleCommandSource(self.__mcdr_server, self)
			elif self.is_player:
				self.__command_source = PlayerCommandSource(self.__mcdr_server, self, self.player)
		return self.__command_source

	def to_command_source(self) -> InfoCommandSource:
		source = self.get_command_source()
		if source is None:
			raise IllegalCallError()
		return source

	def should_send_to_server(self) -> bool:
		return self.__send_to_server

	def cancel_send_to_server(self) -> None:
		self.__send_to_server = False

	# --------------------------------
	#   Formatting and Magic methods
	# --------------------------------

	def format_text(self):
		try:
			time_message = '{:0>2}:{:0>2}:{:0>2}'.format(self.hour, self.min, self.sec)
		except:
			time_message = 'Invalid'
		return '\n'.join([
			'Time: {}; ID: {}'.format(time_message, self.id),
			'Player: {}; Source: {}; Logging level: {}'.format(self.player, self.source, self.logging_level),
			'Content: {}'.format(self.content),
			'Raw content: {}'.format(self.raw_content)
		])

	def __str__(self):
		return '; '.join(self.format_text().splitlines())

	def __deepcopy__(self, memo):
		"""
		Just dont copy the mcdr_server instance
		"""
		existed = memo.get(self)
		if existed is not None:
			return existed
		memo[self] = dupe = Info()
		dupe.hour, dupe.min, dupe.sec = self.hour, self.min, self.sec
		dupe.raw_content = self.raw_content
		dupe.content = self.content
		dupe.player = self.player
		dupe.source = self.source
		dupe.logging_level = self.logging_level
		return dupe
