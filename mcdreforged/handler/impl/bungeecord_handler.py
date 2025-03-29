import re
from typing import Optional

from typing_extensions import override

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.utils.types.message import MessageText


class BungeecordHandler(AbstractServerHandler):
	"""
	A handler for `Bungeecord <https://github.com/SpigotMC/BungeeCord>`__ servers
	"""
	@override
	def get_stop_command(self) -> str:
		return 'end'

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return None

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		from mcdreforged.handler.impl import VanillaHandler
		return 'alertraw {}'.format(VanillaHandler.format_message(message, server_information=server_information))

	@classmethod
	@override
	def get_content_parsing_formatter(cls) -> re.Pattern:
		# 09:00:02 [信息] Listening on /0.0.0.0:25565
		# 09:00:01 [信息] [Steve] -> UpstreamBridge has disconnected
		return re.compile(
			r'(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+)'
			r' \[(?P<logging>[^]]+)]'
			r' (?P<content>.*)'
		)

	__prompt_text_regex = re.compile(r'^>*\r')

	@override
	def pre_parse_server_stdout(self, text):
		text = super().pre_parse_server_stdout(text)
		return self.__prompt_text_regex.sub('', text, 1)

	# [Steve,/127.0.0.1:3631] <-> InitialHandler has connected
	__player_joined_regex = re.compile(r'\[(?P<name>[^,]+),/(.*?)] <-> InitialHandler has connected')

	@override
	def parse_player_joined(self, info: Info) -> Optional[str]:
		if not info.is_user:
			if (m := self.__player_joined_regex.fullmatch(info.content)) is not None:
				return m['name']
		return None

	__player_left_regex = re.compile(r'\[(?P<name>[^]]+)] -> UpstreamBridge has disconnected')

	@override
	def parse_player_left(self, info):
		# [Steve] -> UpstreamBridge has disconnected
		if not info.is_user:
			if (m := self.__player_left_regex.fullmatch(info.content)) is not None:
				return m['name']
		return None

	@override
	def parse_server_version(self, info: Info):
		return None

	__server_address_regex = re.compile(r'Listening on /(?P<ip>\S+):(?P<port>\d+)')

	@override
	def parse_server_address(self, info: Info):
		# Listening on /0.0.0.0:25577
		if not info.is_user:
			if (m := self.__server_address_regex.fullmatch(info.content)) is not None:
				return m['ip'], int(m['port'])
		return None

	__server_startup_done_regex = __server_address_regex

	@override
	def test_server_startup_done(self, info: Info) -> bool:
		# Listening on /0.0.0.0:25577
		return not info.is_user and self.__server_startup_done_regex.fullmatch(info.content) is not None

	@override
	def test_rcon_started(self, info: Info) -> bool:
		return self.test_server_startup_done(info)

	__server_stopping_regex = re.compile(r'Closing listener \[id: .+, L:[\d:/]+]')

	@override
	def test_server_stopping(self, info: Info) -> bool:
		# Closing listener [id: 0x3acae0b0, L:/0:0:0:0:0:0:0:0:25565]
		return not info.is_user and self.__server_stopping_regex.fullmatch(info.content) is not None
