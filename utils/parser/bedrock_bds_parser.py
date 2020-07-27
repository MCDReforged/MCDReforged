from utils.info import Info
from utils.parser.abstract_parser import AbstractParser


class BedrockBDSParser(AbstractParser):
	def parse_server_stdout(self, text: str) -> Info:
		# [2020-07-27 16:38:43 INFO] Starting Server
		pass

	def parse_player_joined(self, info: Info):
		pass

	def parse_player_left(self, info: Info):
		pass

	def parse_death_message(self, info: Info) -> bool:
		pass

	def parse_player_made_advancement(self, info: Info):
		pass

	def pre_parse_server_stdout(self, text: str) -> str:
		pass

	def parse_server_startup_done(self, info: Info) -> bool:

		pass

	def parse_rcon_started(self, info: Info) -> bool:
		pass

	def parse_server_stopping(self, info: Info) -> bool:
		pass