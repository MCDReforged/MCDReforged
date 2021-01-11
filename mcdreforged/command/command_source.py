from typing import TYPE_CHECKING, Any

from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.info import Info
	from mcdreforged.plugin.server_interface import ServerInterface


class CommandSourceType:
	PLAYER = 0
	CONSOLE = 1


class CommandSource:
	source_type: int

	def __init__(self, mcdr_server: 'MCDReforgedServer', info: 'Info', source_type: int):
		self._mcdr_server = mcdr_server
		self._info = info
		self.source_type = source_type

	@property
	def is_player(self) -> bool:
		raise NotImplementedError()

	def get_server(self) -> 'ServerInterface':
		return self._mcdr_server.server_interface

	def get_info(self) -> 'Info':
		return self._info

	def get_permission_level(self) -> int:
		return self._mcdr_server.permission_manager.get_permission(self)

	def has_permission(self, level: int) -> bool:
		return self.get_permission_level() >= level

	def has_permission_higher_than(self, level: int) -> bool:
		return self.get_permission_level() > level

	def reply(self, message: Any, **kwargs):
		"""
		Reply to the command source
		:param message: The message you want to send. It will be mapped with str() unless it's a RTextBase
		"""
		raise NotImplementedError()

	def __str__(self):
		raise NotImplementedError()


class PlayerCommandSource(CommandSource):
	def __init__(self, mcdr_server, info, player: str):
		if not info.is_from_server:
			raise TypeError('{} should be built from server info'.format(self.__class__.__name__))
		super().__init__(mcdr_server, info, CommandSourceType.PLAYER)
		self.player = player

	@property
	def is_player(self):
		return True

	def reply(self, message: Any, **kwargs):
		"""
		Specify key word argument encoding
		"""
		self._mcdr_server.server_interface.tell(self.player, message, encoding=kwargs.get('encoding'), is_plugin_call=False)

	def __str__(self):
		return 'Player {}'.format(self.player)

	def __repr__(self):
		return '{}[player={}]'.format(type(self).__name__, self.player)


class ConsoleCommandSource(CommandSource):
	def __init__(self, mcdr_server, info):
		if not info.is_from_console:
			raise TypeError('{} should be built from console info'.format(self.__class__.__name__))
		super().__init__(mcdr_server, info, CommandSourceType.CONSOLE)

	@property
	def is_player(self):
		return False

	def reply(self, message: Any, **kwargs):
		misc_util.print_text_to_console(self._mcdr_server.logger, message)

	def __str__(self):
		return 'Console'

	def __repr__(self):
		return type(self).__name__
