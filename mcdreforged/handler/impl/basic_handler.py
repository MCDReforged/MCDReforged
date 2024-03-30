"""
The basic plain handler
"""
from typing import Optional, Tuple

from typing_extensions import override

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types.message import MessageText


class BasicHandler(AbstractServerHandler):
	"""
	The basic plain handler, providing the minimum parsed information

	It's used as the fallback handler when every other dedicated handler failed
	"""
	@override
	def get_stop_command(self) -> str:
		return ''

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@classmethod
	@override
	def get_content_parsing_formatter(cls):
		raise RuntimeError()

	@override
	def parse_server_stdout(self, text: str) -> Info:
		return self._get_server_stdout_raw_result(text)

	@override
	def parse_player_joined(self, info):
		return None

	@override
	def parse_player_left(self, info):
		return None

	@override
	def parse_server_version(self, info: Info) -> Optional[str]:
		return None

	@override
	def parse_server_address(self, info: Info) -> Optional[Tuple[str, int]]:
		return None

	@override
	def test_server_startup_done(self, info) -> bool:
		return False

	@override
	def test_rcon_started(self, info: Info) -> bool:
		return False

	@override
	def test_server_stopping(self, info: Info) -> bool:
		return False
