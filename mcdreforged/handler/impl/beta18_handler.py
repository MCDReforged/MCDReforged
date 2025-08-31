import re
from typing import Optional

from typing_extensions import override

from mcdreforged.handler.impl import AbstractMinecraftHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.utils import string_utils
from mcdreforged.utils.types.message import MessageText


class Beta18Handler(AbstractMinecraftHandler):
	"""
	Yes, a handler for Minecraft beta 1.8
	"""
	@classmethod
	@override
	def format_message(cls, message: MessageText, *, server_information: Optional[ServerInformation] = None) -> str:
		if isinstance(message, RTextBase):
			content = message.to_plain_text()
		else:
			content = str(message)
		return string_utils.clean_minecraft_color_code(content)

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return 'tell {} {}'.format(target, self.format_message(message))

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return 'say {}'.format(self.format_message(message))

	# 2020-12-27 02:56:35 [INFO] Loading properties
	# 2020-12-27 02:57:42 [INFO] <Steve> ping
	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> re.Pattern:
		# YYYY-mm-dd HH:MM:SS [LEVEL] MESSAGE
		return re.compile(
			r'(\d+)-(\d+)-(\d+)'
			r' (?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)'
			r' \[(?P<logging>[^]]+)]'
			r' (?P<content>.*)'
		)

	# (beta1.8) Steve [/127.0.0.1:2993] logged in with entity id 3827 at (-130.5, 69.0, 253.5)
	# (mc>=1.0) Alex[/127.0.0.1:5527] logged in with entity id 747 at (176.21, 65.0, 258.03)
	__player_joined_regex = re.compile(r'(?P<name>[^\[ ]+)( )?\[(.*?)] logged in with entity id \d+ at \(.+\)')

	@override
	def parse_player_joined(self, info) -> Optional[str]:
		if not info.is_user:
			if (m := self.__player_joined_regex.fullmatch(info.content)) is not None:
				if self.validate_player_name(m['name']):
					return m['name']
		return None

	# Steve lost connection: disconnect.quitting
	__player_left_regex = re.compile(r'(?P<name>[^ ]+) lost connection: .*')

	@override
	def parse_player_left(self, info: Info) -> Optional[str]:
		if info.content is not None and info.is_from_server and (m := self.__player_left_regex.fullmatch(info.content)) is not None:
			return m['name']
		return None

	# (beta1.8) Done (6368115300ns)! For help, type "help" or "?"
	# (mc>=1.0) Done (0.295s)! For help, type "help" or "?"
	__server_startup_done_regex = re.compile(r'Done \([0-9.]+n?s\)! For help, type "help" or "\?"')

	@override
	def test_server_startup_done(self, info: Info) -> bool:
		return info.content is not None and not info.is_user and self.__server_startup_done_regex.fullmatch(info.content) is not None

	@override
	def test_rcon_started(self, info: Info) -> bool:
		return False

	@override
	def test_server_stopping(self, info: Info) -> bool:
		# Stopping server
		return not info.is_user and info.content == 'Stopping server'
