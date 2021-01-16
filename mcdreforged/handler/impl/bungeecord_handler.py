import re
from typing import Any, Optional

from parse import parse

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.handler.impl.beta18_handler import Beta18Handler
from mcdreforged.info import Info


class BungeecordHandler(AbstractServerHandler):
	def get_stop_command(self) -> str:
		return 'end'

	def get_send_message_command(self, target: str, message: Any) -> Optional[str]:
		return None

	def get_broadcast_message_command(self, message: Any) -> Optional[str]:
		return 'alertraw {}'.format(Beta18Handler.format_message(message))

	@classmethod
	def get_content_parsing_formatter(cls):
		# 09:00:02 [信息] Listening on /0.0.0.0:25565
		# 09:00:01 [信息] [Steve] -> UpstreamBridge has disconnected
		return '{hour:d}:{min:d}:{sec:d} [{logging}] {content}'

	def parse_server_stdout(self, text):
		result = self._get_server_stdout_raw_result(text)
		self._content_parse(result)
		return result

	def pre_parse_server_stdout(self, text):
		text = super().pre_parse_server_stdout(text)
		match = re.match(r'>*\r', text)
		if match is not None:
			text = text.replace(match.group(), '', 1)
		return text

	def parse_player_joined(self, info: Info) -> Optional[str]:
		# [Steve,/127.0.0.1:3631] <-> InitialHandler has connected
		if not info.is_user:
			parsed = parse('[{name},/{ip}] <-> InitialHandler has connected', info.content)
			if parsed is not None:
				return parsed['name']
		return None

	def parse_player_left(self, info):
		# [Steve] -> UpstreamBridge has disconnected
		if not info.is_user:
			parsed = parse('[{name}] -> UpstreamBridge has disconnected', info.content)
			if parsed is not None:
				return parsed['name']
		return None

	def test_server_startup_done(self, info: Info) -> bool:
		# Listening on /0.0.0.0:25577
		return not info.is_user and re.fullmatch(r'Listening on /[0-9.]+:[0-9]+', info.content) is not None

	def test_rcon_started(self, info: Info) -> bool:
		return self.test_server_startup_done(info)

	def test_server_stopping(self, info: Info) -> bool:
		# Closing listener [id: 0x3acae0b0, L:/0:0:0:0:0:0:0:0:25565]
		return not info.is_user and re.fullmatch(r'Closing listener \[id: .+, L:[\d:/]+\]', info.content) is not None
