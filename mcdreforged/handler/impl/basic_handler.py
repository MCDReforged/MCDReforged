"""
The basic plain handler
"""
from typing import Any, Optional, Tuple

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation


class BasicHandler(AbstractServerHandler):
	def get_stop_command(self) -> str:
		return ''

	def get_send_message_command(self, target: str, message: Any, server_information: ServerInformation) -> Optional[str]:
		return None

	def get_broadcast_message_command(self, message: Any, server_information: ServerInformation) -> Optional[str]:
		return None

	@classmethod
	def get_content_parsing_formatter(cls):
		raise RuntimeError()

	def parse_server_stdout(self, text: str) -> Info:
		return self._get_server_stdout_raw_result(text)

	def parse_player_joined(self, info):
		return None

	def parse_player_left(self, info):
		return None

	def parse_server_version(self, info: Info) -> Optional[str]:
		return None

	def parse_server_address(self, info: Info) -> Optional[Tuple[str, int]]:
		return None

	def test_server_startup_done(self, info) -> bool:
		return False

	def test_rcon_started(self, info: Info) -> bool:
		return False

	def test_server_stopping(self, info: Info) -> bool:
		return False
