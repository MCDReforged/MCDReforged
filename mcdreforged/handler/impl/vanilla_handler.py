import json
import re
from typing import Optional, Any

from parse import parse

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info import Info
from mcdreforged.minecraft.rtext import RTextBase


class VanillaHandler(AbstractServerHandler):
	def get_stop_command(self) -> str:
		return 'stop'

	def get_send_message_command(self, target: str, message: Any) -> Optional[str]:
		if isinstance(message, RTextBase):
			content = message.to_json_str()
		else:
			content = json.dumps(str(message))
		return 'tellraw {} {}'.format(target, content)

	def get_broadcast_message_command(self, message: Any) -> Optional[str]:
		return self.get_send_message_command('@a', message)

	@classmethod
	def get_content_parsing_formatter(cls):
		return '[{hour:d}:{min:d}:{sec:d}] [{thread}/{logging}]: {content}'

	@classmethod
	def _verify_player_name(cls, name: str):
		return re.fullmatch(r'\w+', name) is not None

	def parse_server_stdout(self, text: str):
		result = self._get_server_stdout_raw_result(text)
		self._content_parse(result)
		parsed = parse('<{name}> {message}', result.content)
		if parsed is not None and self._verify_player_name(parsed['name']):
			result.player, result.content = parsed['name'], parsed['message']
		return result

	def parse_player_joined(self, info: Info):
		# Steve[/127.0.0.1:9864] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
		if not info.is_user:
			parsed = parse('{name}[{}] logged in with entity id {} at ({})', info.content)
			if parsed is not None and self._verify_player_name(parsed['name']):
				return parsed['name']
		return None

	def parse_player_left(self, info: Info):
		# Steve left the game
		if not info.is_user and re.fullmatch(r'\w{1,16} left the game', info.content):
			return info.content.split(' ')[0]
		return None

	def test_server_startup_done(self, info: Info):
		# 1.13+ Done (3.500s)! For help, type "help"
		# 1.13- Done (3.500s)! For help, type "help" or "?"
		return info.is_from_server and re.fullmatch(r'Done \([0-9.]*s\)! For help, type "help"( or "\?")?', info.content) is not None

	def test_rcon_started(self, info: Info):
		# RCON running on 0.0.0.0:25575
		return info.is_from_server and re.fullmatch(r'RCON running on [\w.]+:\d+', info.content) is not None

	def test_server_stopping(self, info: Info):
		# Stopping server
		return info.is_from_server and info.content == 'Stopping server'
