import json
import re
import time
from typing import Optional, Tuple, List, Iterable

from typing_extensions import override, assert_never

from mcdreforged.handler.handler_spec import HandlerSpec, TextTransform, TextTransforms, StopMethod, SendMessageMethod, SendMessageMethods, \
	BroadcastMessageMethod, BroadcastMessageMethods
from mcdreforged.handler.impl import mc_version_utils
from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.info_reactor.info import Info, InfoSource
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.minecraft.rtext.text import RTextBase, RTextJsonFormat
from mcdreforged.utils import string_utils
from mcdreforged.utils.types.message import MessageText


class SpecServerHandler(ServerHandler):
	"""
	A server handler that works according to a :class:`~mcdreforged.handler.handler_spec.HandlerSpec`

	:param spec: The handler spec of this handler

	.. versionadded:: v2.17.0
	"""

	def __init__(self, spec: HandlerSpec):
		self.__spec = spec

	@property
	def spec(self) -> HandlerSpec:
		"""
		The handler spec of this handler
		"""
		return self.__spec

	@override
	def get_name(self) -> str:
		return self.__spec.name

	# ------------------
	#   Server control
	# ------------------

	@override
	def get_stop_method(self) -> StopMethod:
		return self.__spec.control.stop

	@classmethod
	def __format_json_message(cls, message: MessageText, server_information: ServerInformation) -> str:
		if isinstance(message, RTextBase):
			json_format = mc_version_utils.get_rtext_json_format(server_information.version) if server_information else RTextJsonFormat.default()
			return message.to_json_str(json_format=json_format)
		else:
			return json.dumps(str(message), ensure_ascii=False, separators=(',', ':'))

	@classmethod
	def __format_plain_message(cls, message: MessageText) -> str:
		content = message.to_plain_text() if isinstance(message, RTextBase) else str(message)
		return string_utils.clean_minecraft_color_code(content)

	@classmethod
	def __tellraw_command(cls, target: str, message: MessageText, server_information: ServerInformation) -> str:
		try:
			can_do_execute = mc_version_utils.does_mc_version_has_execute_command(server_information.version)
		except (ValueError, IndexError):
			can_do_execute = False

		command = 'tellraw {} {}'.format(target, cls.__format_json_message(message, server_information))
		if can_do_execute:
			# Mute the "No player was found" output when no player is online
			command = 'execute at @p run ' + command
		return command

	def __render_message_command(self, method: SendMessageMethod | BroadcastMessageMethod | None, target: Optional[str], message: MessageText, server_information: ServerInformation) -> Optional[str]:
		if method is None:
			return None
		elif isinstance(method, (SendMessageMethods.Builtin, BroadcastMessageMethods.Builtin)):
			if isinstance(method, BroadcastMessageMethods.Builtin):
				target = method.target
			assert target is not None
			match method.builtin:
				case method.Name.minecraft_tellraw:
					return self.__tellraw_command(target, message, server_information)
				case _:
					assert_never(method.builtin)
		elif isinstance(method, (SendMessageMethods.Template, BroadcastMessageMethods.Template)):
			match method.message_format:
				case method.Format.json:
					formatted = self.__format_json_message(message, server_information)
				case method.Format.plain:
					formatted = self.__format_plain_message(message)
				case _:
					assert_never(method.message_format)
			return method.template.format(target=target, message=formatted)
		else:
			assert_never(method)

	@override
	def get_send_message_command(self, target: str, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return self.__render_message_command(self.__spec.control.send_message, target, message, server_information)

	@override
	def get_broadcast_message_command(self, message: MessageText, server_information: ServerInformation) -> Optional[str]:
		return self.__render_message_command(self.__spec.control.broadcast_message, None, message, server_information)

	# -------------------------
	#   Server output parsing
	# -------------------------

	@classmethod
	def __apply_text_transforms(cls, text: str, transforms: Iterable[TextTransform]) -> str:
		for transform in transforms:
			if isinstance(transform, TextTransforms.Builtin):
				match transform.builtin:
					case TextTransforms.Builtin.Name.strip_ansi_color:
						text = string_utils.clean_console_color_code(text)
					case TextTransforms.Builtin.Name.strip_minecraft_color:
						text = string_utils.clean_minecraft_color_code(text)
					case _:
						assert_never(transform.builtin)
			elif isinstance(transform, TextTransforms.Sub):
				text = transform.sub.sub(transform.repl, text, transform.count)
			else:
				assert_never(transform)
		return text

	@override
	def pre_parse_server_stdout(self, text: str) -> str:
		return self.__apply_text_transforms(text, self.__spec.parsing.pre_parse)

	@override
	def parse_console_command(self, text: str) -> Info:
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		info = Info(InfoSource.CONSOLE, text)
		t = time.localtime(time.time())
		info.hour = t.tm_hour
		info.min = t.tm_min
		info.sec = t.tm_sec
		info.content = text
		return info

	@override
	def parse_server_stdout(self, text: str) -> Info:
		if type(text) is not str:
			raise TypeError('The text to parse should be a string')
		info = Info(InfoSource.SERVER, text)
		content = self.__apply_text_transforms(text, self.__spec.parsing.line_transforms)

		for pattern in self.__spec.parsing.line:
			if (m := pattern.fullmatch(content)) is not None:
				break
		else:
			raise ValueError('Unrecognized input: ' + content)

		groups = m.groupdict()
		info.hour = int(groups['hour']) if groups.get('hour') is not None else None
		info.min = int(groups['min']) if groups.get('min') is not None else None
		info.sec = int(groups['sec']) if groups.get('sec') is not None else None
		info.logging_level = groups.get('logging')
		info.content = m['content']

		if (m := self.__match_with_player_name(self.__spec.parsing.player_message, info.content)) is not None:
			info.player, info.content = m['name'], m['message']
		return info

	def __match_with_player_name(self, patterns: List[re.Pattern[str]], text: str) -> Optional[re.Match[str]]:
		for pattern in patterns:
			if (m := pattern.fullmatch(text)) is not None and self.validate_player_name(m['name']):
				return m
		return None

	def __match_event(self, patterns: List[re.Pattern[str]], info: Info, *, with_player_name: bool) -> Optional[re.Match[str]]:
		if info.content is None or not info.is_from_server or info.player is not None:
			return None
		if with_player_name:
			return self.__match_with_player_name(patterns, info.content)
		for pattern in patterns:
			if (m := pattern.fullmatch(info.content)) is not None:
				return m
		return None

	@override
	def parse_player_joined(self, info: Info) -> Optional[str]:
		if (m := self.__match_event(self.__spec.events.player_joined, info, with_player_name=True)) is not None:
			return m['name']
		return None

	@override
	def parse_player_left(self, info: Info) -> Optional[str]:
		if (m := self.__match_event(self.__spec.events.player_left, info, with_player_name=True)) is not None:
			return m['name']
		return None

	@override
	def parse_server_version(self, info: Info) -> Optional[str]:
		if (m := self.__match_event(self.__spec.events.server_version, info, with_player_name=False)) is not None:
			return m['version']
		return None

	@override
	def parse_server_address(self, info: Info) -> Optional[Tuple[str, int]]:
		if (m := self.__match_event(self.__spec.events.server_address, info, with_player_name=False)) is not None:
			return m['ip'], int(m['port'])
		return None

	@override
	def test_server_startup_done(self, info: Info) -> bool:
		return self.__match_event(self.__spec.events.server_startup_done, info, with_player_name=False) is not None

	@override
	def test_rcon_started(self, info: Info) -> bool:
		return self.__match_event(self.__spec.events.rcon_started, info, with_player_name=False) is not None

	@override
	def test_server_stopping(self, info: Info) -> bool:
		return self.__match_event(self.__spec.events.server_stopping, info, with_player_name=False) is not None

	@override
	def validate_player_name(self, name: str) -> bool:
		return self.__spec.parsing.player_name.fullmatch(name) is not None
