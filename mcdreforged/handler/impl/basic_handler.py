"""
The basic plain handler
"""
import time
from typing import Optional, Tuple

from typing_extensions import override

from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.info_reactor.info import Info, InfoSource
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types.message import MessageText


class BasicHandler(ServerHandler):
	"""
	The basic plain handler, providing the minimum parsed information

	It's used as the fallback handler when every other dedicated handler failed
	"""

	@override
	def get_name(self) -> str:
		return 'basic_handler'

	@override
	def get_stop_command(self) -> str:
		return ''

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@override
	def pre_parse_server_stdout(self, text: str) -> str:
		return text

	@override
	def parse_console_command(self, text: str) -> Info:
		info = Info(InfoSource.CONSOLE, text)
		t = time.localtime(time.time())
		info.hour = t.tm_hour
		info.min = t.tm_min
		info.sec = t.tm_sec
		info.content = text
		return info

	@override
	def parse_server_stdout(self, text: str) -> Info:
		info = Info(InfoSource.SERVER, text)
		info.content = text
		return info

	@override
	def parse_player_joined(self, info: Info) -> Optional[str]:
		return None

	@override
	def parse_player_left(self, info: Info) -> Optional[str]:
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
