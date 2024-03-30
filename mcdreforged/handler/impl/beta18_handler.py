import re
from typing import Optional

import parse
from typing_extensions import override

from mcdreforged.handler.impl.vanilla_handler import VanillaHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.utils import string_util
from mcdreforged.utils.types import MessageText


class Beta18Handler(VanillaHandler):
	"""
	Yes, a handler for Minecraft beta 1.8
	"""
	@classmethod
	@override
	def format_message(cls, message: MessageText) -> str:
		if isinstance(message, RTextBase):
			content = message.to_plain_text()
		else:
			content = str(message)
		return string_util.clean_minecraft_color_code(content)

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
	def get_content_parsing_formatter(cls):
		return '{y:d}-{m:d}-{d:d} {hour:d}:{min:d}:{sec:d} [{logging}] {content}'

	__player_joined_parser = parse.Parser('{name} [{}] logged in with entity id {} at ({})')
	__player_left_parser = parse.Parser('{name} lost connection: {}')
	__server_startup_done_regex = re.compile(r'Done \([0-9.]*ns\)! For help, type "help" or "\?"')

	@override
	def parse_player_joined(self, info):
		# Steve [/127.0.0.1:2993] logged in with entity id 3827 at (-130.5, 69.0, 253.5)
		if not info.is_user:
			# there's an extra space character after {name}
			parsed = self.__player_joined_parser.parse(info.content)
			if parsed is not None and self._verify_player_name(parsed['name']):
				return parsed['name']
		return None

	@override
	def parse_player_left(self, info: Info):
		# Steve lost connection: disconnect.quitting
		if info.is_from_server and self.__player_left_parser.parse(info.content) is not None:
			return info.content.split(' ')[0]
		return None

	@override
	def test_server_startup_done(self, info: Info):
		# Done (6368115300ns)! For help, type "help" or "?"
		if info.is_user:
			return False
		match = self.__server_startup_done_regex.fullmatch(info.content)
		return match is not None

	@override
	def test_rcon_started(self, info: Info):
		return False

	@override
	def test_server_stopping(self, info: Info):
		# Stopping server
		return not info.is_user and info.content == 'Stopping server'
