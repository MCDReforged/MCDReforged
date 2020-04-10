# -*- coding: utf-8 -*-


class InfoSource:
	# the text is from the stdout of the server
	SERVER = 0

	# the text is from user input
	CONSOLE = 1


class Info:
	def __init__(self):
		# time information from the parsed text
		self.hour = None
		self.min = None
		self.sec = None

		# the name of the player. if it's not sent by a player the value will be None
		self.player = None

		# very raw content
		self.raw_content = None

		# if the text is sent by a player the value will be what the player said. if not the value will be the pain text
		self.content = None

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

