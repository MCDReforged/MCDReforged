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
		self.second = None

		# the name of the player. if it's not sent by a player the value will be None
		self.player = None

		# if the text is sent by a player the value will be what the player said. if not the value will be the pain text
		self.content = None

		# the value type is InfoSource
		self.source = None

	@property
	def is_user(self):
		return self.source == InfoSource.CONSOLE or self.player is not None