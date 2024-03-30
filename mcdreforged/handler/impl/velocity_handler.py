import re
from typing import Optional, Union, Iterable

import parse
from typing_extensions import override

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types import MessageText


class VelocityHandler(AbstractServerHandler):
	"""
	A handler for `Velocity <https://velocitypowered.com>`__ servers
	"""
	@override
	def get_stop_command(self) -> str:
		return 'shutdown'

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> Union[str, Iterable[str]]:
		# It's the same as WaterfallHandler, but since it's a different server here comes an individual copy
		return (
			'[{hour:d}:{min:d}:{sec:d} {logging}]: {content}',
			'[{hour:d}:{min:d}:{sec:d} {logging}] {dummy}: {content}'  # something there is an extra element after the heading [] and :
		)

	__player_joined_parser = parse.Parser('[connected player] {name} (/{address}) has connected')
	__player_left_parser = parse.Parser('[connected player] {name} (/{address}) has disconnected')
	__server_address_parser = parse.Parser('Listening on /{}:{:d}')
	__server_startup_done_regex = re.compile(r'Done \([0-9.]*s\)!')

	@override
	def parse_player_joined(self, info: Info) -> Optional[str]:
		# [connected player] Fallen_Breath (/127.0.0.1:12896) has connected
		if not info.is_user:
			parsed = self.__player_joined_parser.parse(info.content)
			if parsed is not None:
				return parsed['name']
		return None

	@override
	def parse_player_left(self, info: Info) -> Optional[str]:
		# [connected player] Fallen_Breath (/127.0.0.1:12896) has disconnected
		if not info.is_user:
			parsed = self.__player_left_parser.parse(info.content)
			if parsed is not None:
				return parsed['name']
		return None

	@override
	def parse_server_version(self, info: Info):
		return None

	@override
	def parse_server_address(self, info: Info):
		# Listening on /192.168.0.1:25577
		# Listening on /[0:0:0:0:0:0:0:0%0]:25577
		# Listening on /0:0:0:0:0:0:0:0%0:25577
		if not info.is_user:
			parsed = self.__server_address_parser.parse(info.content)
			if parsed is not None:
				return parsed[0], parsed[1]
		return None

	@override
	def test_server_startup_done(self, info: Info) -> bool:
		# Done (3.05s)!
		return not info.is_user and self.__server_startup_done_regex.fullmatch(info.content) is not None

	@override
	def test_rcon_started(self, info: Info) -> bool:
		return False

	@override
	def test_server_stopping(self, info: Info) -> bool:
		# Shutting down the proxy...
		return not info.is_user and info.content == 'Shutting down the proxy...'
