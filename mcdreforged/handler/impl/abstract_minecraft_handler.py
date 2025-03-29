import functools
import json
import re
from abc import ABC
from typing import Optional, List, Tuple

import parse
from typing_extensions import override

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.minecraft.rtext.text import RTextBase, RTextJsonFormat
from mcdreforged.utils import string_utils
from mcdreforged.utils.types.message import MessageText


def __check_mc_version_ge(version_name: Optional[str], min_release: Tuple[int, ...], min_snapshot: Tuple[int, int]) -> bool:
	if version_name is None:
		return False

	def check_release_version(major: str, minor: str, patch: Optional[str]) -> bool:
		if patch is None:
			patch = '0'
		return (int(major), int(minor), int(patch)) >= min_release

	version_with_release_regex = [
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))?', re.IGNORECASE),  # "1.21", "1.17.1"
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))? Pre-Release \d+', re.IGNORECASE),  # "1.20.5 Pre-Release 4"
		re.compile(r'(?P<major>\d+)\.(?P<minor>\d+)(\.(?P<patch>\d+))? Release Candidate \d+', re.IGNORECASE),  # "1.21 Release Candidate 1"
	]
	for regex in version_with_release_regex:
		if (m := regex.fullmatch(version_name)) is not None:
			return check_release_version(m.group('major'), m.group('minor'), m.group('patch'))

	# modern snapshots, e.g. "22w45a"
	if (m := re.fullmatch(r'(\d{2})w(\d{2})[a-z]', version_name)) is not None:
		return (int(m.group(1)), int(m.group(2))) >= min_snapshot

	# unknown version
	return False


@functools.lru_cache(maxsize=128)
def _does_mc_version_has_execute_command(version_name: Optional[str]) -> bool:
	# >= 18w30a, first 1.13.1 snapshot
	return __check_mc_version_ge(version_name, (1, 13, 0), (18, 30))


@functools.lru_cache(maxsize=128)
def _get_rtext_json_format(version_name: Optional[str]) -> RTextJsonFormat:
	# >= 25w03a, an 1.21.5 snapshot
	if __check_mc_version_ge(version_name, (1, 21, 5), (25, 3)):
		return RTextJsonFormat.V_1_21_5
	else:
		return RTextJsonFormat.default()


class AbstractMinecraftHandler(AbstractServerHandler, ABC):
	"""
	An abstract handler for Minecraft Java Edition servers
	"""
	@override
	def get_stop_command(self) -> str:
		return 'stop'

	@classmethod
	def get_player_message_parsing_formatter(cls) -> List[re.Pattern]:
		"""
		Return a list of :external:class:`re.Pattern` that is used in method :meth:`parse_server_stdout` for parsing player message

		These regex patterns are supposed to contain at least the following fields:

		- ``name``, the name of the player
		- ``message``, what the player said

		The return value of the first succeeded :external:meth:`re.Pattern.fullmatch` call will be used
		for filling fields of the :class:`~mcdreforged.info_reactor.info.Info` object

		If none of these formatter strings can be parsed successfully, then this info
		is considered as a non-player message, i.e. has :attr:`info.player <mcdreforged.info_reactor.info.Info.hour>` equaling None
		"""
		return [
			re.compile(r'(\[Not Secure] )?<(?P<name>[^>]+)> (?P<message>.*)')
		]

	@classmethod
	@functools.lru_cache()
	def __get_player_message_parsers(cls) -> List[re.Pattern]:
		"""
		The return value is cached for reuse. Do not modify
		"""
		# TODO: drop parse.Parser support
		formatters = cls.get_player_message_parsing_formatter()
		return [parse.Parser(fmt) if isinstance(fmt, str) else fmt for fmt in formatters]

	@classmethod
	def format_message(cls, message: MessageText, *, server_information: Optional[ServerInformation] = None) -> str:
		"""
		A utility method to convert a message into a valid argument used in message sending command
		"""
		if isinstance(message, RTextBase):
			json_format = _get_rtext_json_format(server_information.version) if server_information else RTextJsonFormat.default()
			return message.to_json_str(json_format=json_format)
		else:
			# quote it
			return json.dumps(str(message), ensure_ascii=False, separators=(',', ':'))

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		try:
			can_do_execute = _does_mc_version_has_execute_command(server_information.version)
		except (ValueError, IndexError):
			# TODO: logging?
			can_do_execute = False

		command = 'tellraw {} {}'.format(target, self.format_message(message, server_information=server_information))
		if can_do_execute:
			# Mute the "No player was found" output when no player is online by using the "execute at" command
			command = 'execute at @p run ' + command
		return command

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return self.get_send_message_command('@a', message, server_information)

	@classmethod
	@override
	def _get_server_stdout_raw_result(cls, text: str) -> Info:
		raw_result = super()._get_server_stdout_raw_result(text)
		# Minecraft <= 1.12.x might output minecraft color codes to the console
		# Just remove that
		raw_result.content = string_utils.clean_minecraft_color_code(raw_result.content)
		return raw_result

	__player_name_regex = re.compile(r'[a-zA-Z0-9_]{3,16}')

	@classmethod
	def _verify_player_name(cls, name: str):
		return cls.__player_name_regex.fullmatch(name) is not None

	@override
	def parse_server_stdout(self, text: str):
		result = super().parse_server_stdout(text)

		for parser in self.__get_player_message_parsers():
			if isinstance(parser, parse.Parser):
				parsed = parser.parse(result.content)  # TODO: drop parse.Parser support
			else:
				parsed = parser.fullmatch(result.content)
			if parsed is not None and self._verify_player_name(parsed['name']):
				result.player, result.content = parsed['name'], parsed['message']
				break

		return result

	# Steve[/127.0.0.1:9864] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
	# Steve[/[2001:db8:85a3::8a2e:370:7334]:9864] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
	# Steve[local] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
	# Steve[IP hidden] logged in with entity id 131 at (187.2703, 146.79014, 404.84718)
	__player_joined_regex = re.compile(r'(?P<name>[^\[]+)\[(.*?)] logged in with entity id \d+ at \(.+\)')

	@override
	def parse_player_joined(self, info: Info):
		if not info.is_user:
			if (m := self.__player_joined_regex.fullmatch(info.content)) is not None:
				if self._verify_player_name(m['name']):
					return m['name']
		return None

	# Steve left the game
	__player_left_regex = re.compile(r'(?P<name>[^ ]+) left the game')

	@override
	def parse_player_left(self, info: Info):
		if not info.is_user:
			if (m := self.__player_left_regex.fullmatch(info.content)) is not None:
				if self._verify_player_name(m['name']):
					return m['name']
		return None

	__server_version_regex = re.compile(r'Starting minecraft server version (?P<version>.+)')

	@override
	def parse_server_version(self, info: Info):
		if not info.is_user:
			if (m := self.__server_version_regex.fullmatch(info.content)) is not None:
				return m['version']
		return None

	__server_address_regex = re.compile(r'Starting Minecraft server on (?P<ip>\S+):(?P<port>\d+)')

	@override
	def parse_server_address(self, info: Info):
		if not info.is_user:
			if (m := self.__server_address_regex.fullmatch(info.content)) is not None:
				return m['ip'], int(m['port'])
		return None

	# 1.13+ Done (3.500s)! For help, type "help"
	# 1.13- Done (3.500s)! For help, type "help" or "?"
	__server_startup_done_regex = re.compile(
		r'Done \([0-9.]+s\)! For help, type "help"'
		r'( or "\?")?'  # mc < 1.13
	)

	@override
	def test_server_startup_done(self, info: Info):
		return info.is_from_server and self.__server_startup_done_regex.fullmatch(info.content) is not None

	__rcon_started_regex = re.compile(r'RCON running on [\w.]+:\d+')

	@override
	def test_rcon_started(self, info: Info):
		# RCON running on 0.0.0.0:25575
		return info.is_from_server and self.__rcon_started_regex.fullmatch(info.content) is not None

	@override
	def test_server_stopping(self, info: Info):
		# Stopping server
		return info.is_from_server and info.content == 'Stopping server'
