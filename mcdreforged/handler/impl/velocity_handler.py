import re
from typing import Optional, Union, Iterable, Any

from parse import parse

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation


class VelocityHandler(AbstractServerHandler):
	def get_stop_command(self) -> str:
		return 'shutdown'

	def get_send_message_command(self, target: str, message: Any, server_information: ServerInformation) -> Optional[str]:
		return None

	def get_broadcast_message_command(self, message: Any, server_information: ServerInformation) -> Optional[str]:
		return None

	@classmethod
	def get_content_parsing_formatter(cls) -> Union[str, Iterable[str]]:
		# It's the same as WaterfallHandler, but since it's a different server here comes an individual copy
		return (
			'[{hour:d}:{min:d}:{sec:d} {logging}]: {content}',
			'[{hour:d}:{min:d}:{sec:d} {logging}] {dummy}: {content}'  # somethings there is an extra element after the heading [] and :
		)

	def parse_player_joined(self, info: Info) -> Optional[str]:
		# [connected player] Fallen_Breath (/127.0.0.1:12896) has connected
		if not info.is_user:
			parsed = parse('[connected player] {name} (/{address}) has connected', info.content)
			if parsed is not None:
				return parsed['name']
		return None

	def parse_player_left(self, info: Info) -> Optional[str]:
		# [connected player] Fallen_Breath (/127.0.0.1:12896) has disconnected
		if not info.is_user:
			parsed = parse('[connected player] {name} (/{address}) has disconnected', info.content)
			if parsed is not None:
				return parsed['name']
		return None

	def parse_server_version(self, info: Info):
		return None

	def parse_server_address(self, info: Info):
		# Listening on /192.168.0.1:25577
		# Listening on /[0:0:0:0:0:0:0:0%0]:25577
		# Listening on /0:0:0:0:0:0:0:0%0:25577
		if not info.is_user:
			parsed = parse('Listening on /{}:{:d}', info.content)
			if parsed is not None:
				return parsed[0], parsed[1]
		return None

	def test_server_startup_done(self, info: Info) -> bool:
		# Done (3.05s)!
		return not info.is_user and re.fullmatch(r'Done \([0-9.]*s\)!', info.content) is not None

	def test_rcon_started(self, info: Info) -> bool:
		return False

	def test_server_stopping(self, info: Info) -> bool:
		# Shutting down the proxy...
		return not info.is_user and info.content == 'Shutting down the proxy...'
