from abc import ABC
from typing import TYPE_CHECKING, Any, Optional

from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.info import Info
	from mcdreforged.plugin.server_interface import ServerInterface


class CommandSource:
	@property
	def is_player(self) -> bool:
		raise NotImplementedError()

	@property
	def is_console(self) -> bool:
		raise NotImplementedError()

	def get_server(self) -> 'ServerInterface':
		raise NotImplementedError()

	def get_permission_level(self) -> int:
		raise NotImplementedError()

	def has_permission(self, level: int) -> bool:
		return self.get_permission_level() >= level

	def has_permission_higher_than(self, level: int) -> bool:
		return self.get_permission_level() > level

	def reply(self, message: Any, **kwargs) -> None:
		"""
		Reply to the command source
		:param message: The message you want to send. It will be mapped with str() unless it's a RTextBase
		"""
		raise NotImplementedError()


class InfoCommandSource(CommandSource, ABC):
	"""
	Command source generated from info
	"""
	def __init__(self, mcdr_server: 'MCDReforgedServer', info: 'Info'):
		self._mcdr_server = mcdr_server
		self._info = info

	def get_info(self) -> 'Info':
		return self._info

	def get_server(self) -> 'ServerInterface':
		return self._mcdr_server.server_interface

	def get_permission_level(self) -> int:
		return self._mcdr_server.permission_manager.get_permission(self)


class PlayerCommandSource(InfoCommandSource):
	def __init__(self, mcdr_server, info, player: str):
		if not info.is_from_server:
			raise TypeError('{} should be built from server info'.format(self.__class__.__name__))
		super().__init__(mcdr_server, info)
		self.player = player

	@property
	def is_player(self) -> bool:
		return True

	@property
	def is_console(self) -> bool:
		return False

	def reply(self, message: Any, *, encoding: Optional[str] = None, **kwargs):
		"""
		:keyword encoding: encoding method for server_interface.tell
		"""
		self._mcdr_server.server_interface.tell(self.player, message, encoding=encoding, is_plugin_call=False)

	def __str__(self):
		return 'Player {}'.format(self.player)

	def __repr__(self):
		return '{}[player={}]'.format(type(self).__name__, self.player)


class ConsoleCommandSource(InfoCommandSource):
	def __init__(self, mcdr_server, info):
		if not info.is_from_console:
			raise TypeError('{} should be built from console info'.format(self.__class__.__name__))
		super().__init__(mcdr_server, info)

	@property
	def is_player(self) -> bool:
		return False

	@property
	def is_console(self) -> bool:
		return True

	def reply(self, message: Any, *, console_text: Optional[Any] = None, **kwargs):
		"""
		:keyword console_text: If it's specified, use it instead of param message
		"""
		if console_text is not None:
			message = console_text
		misc_util.print_text_to_console(self._mcdr_server.logger, message)

	def __str__(self):
		return 'Console'

	def __repr__(self):
		return type(self).__name__
