"""
The basic plain parser
"""

from mcdreforged.info import Info
from mcdreforged.parser.abstract_server_handler import AbstractServerHandler


class BasicHandler(AbstractServerHandler):
	def get_stop_command(self) -> str:
		return ''

	def parse_server_stdout(self, text: str) -> Info:
		return self._get_server_stdout_raw_result(text)

	def parse_player_joined(self, info):
		return None

	def parse_player_left(self, info):
		return None

	def test_server_startup_done(self, info) -> bool:
		return False

	def test_rcon_started(self, info: Info) -> bool:
		return False

	def test_server_stopping(self, info: Info) -> bool:
		return False
