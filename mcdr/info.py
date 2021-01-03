"""
Info and InfoSource
"""
from mcdr.command.command_source import CommandSource, ConsoleCommandSource, PlayerCommandSource


class InfoSource:
	# the text is from the stdout of the server
	SERVER = 0

	# the text is from user input
	CONSOLE = 1


class Info:
	id_counter = 0

	def __init__(self):
		# a increasing id number for distinguishing info instance
		Info.id_counter += 1
		self.id = Info.id_counter

		# time information from the parsed text
		self.hour = None
		self.min = None
		self.sec = None

		# very raw content
		self.raw_content = None

		# if the text is sent by a player the value will be what the player said. if not the value will be the pain text
		self.content = None

		# the name of the player. if it's not sent by a player the value will be None
		self.player = None

		# the value type is InfoSource
		self.source = None

		# the logging level of the server's stdout, such as "INFO" or "WARN"
		self.logging_level = None

	@property
	def is_player(self):
		return self.player is not None

	@property
	def is_user(self):
		return self.source == InfoSource.CONSOLE or self.is_player

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


class ServerInfo(Info):
	def __init__(self, mcdr_server):
		super().__init__()
		self.__mcdr_server = mcdr_server

	def to_command_source(self) -> CommandSource or None:
		if self.source == InfoSource.CONSOLE:
			return ConsoleCommandSource(self.__mcdr_server)
		elif self.is_player:
			return PlayerCommandSource(self.__mcdr_server, self.player)
		else:
			return None
