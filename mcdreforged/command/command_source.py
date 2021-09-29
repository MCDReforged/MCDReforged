from abc import ABC
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Optional

from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.info_reactor.info import Info
	from mcdreforged.plugin.server_interface import ServerInterface
	from mcdreforged.plugin.type.plugin import AbstractPlugin
	from mcdreforged.preference.preference_manager import PreferenceItem


class CommandSource(ABC):
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

	def get_preference(self) -> 'PreferenceItem':
		return self.get_server().get_preference(self)

	@contextmanager
	def preferred_language_context(self):
		with RTextMCDRTranslation.language_context(self.get_preference().language):
			yield

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
		self.__info = info

	def get_info(self) -> 'Info':
		return self.__info

	def get_server(self) -> 'ServerInterface':
		return self._mcdr_server.basic_server_interface

	def get_permission_level(self) -> int:
		return self._mcdr_server.permission_manager.get_permission(self)

	def __str__(self):
		raise NotImplementedError()

	def __repr__(self):
		raise NotImplementedError()


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
		self._mcdr_server.basic_server_interface.tell(self.player, message, encoding=encoding)

	def __str__(self):
		return 'Player {}'.format(self.player)

	def __repr__(self):
		return '{}[player={},info_id={}]'.format(type(self).__name__, self.player, self.get_info().id)


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
		with self.preferred_language_context():
			misc_util.print_text_to_console(self._mcdr_server.logger, message)

	def __str__(self):
		return 'Console'

	def __repr__(self):
		return '{}[info_id={}]'.format(type(self).__name__, self.get_info().id)


class PluginCommandSource(CommandSource):
	def __init__(self, server: 'ServerInterface', plugin: Optional['AbstractPlugin'] = None):
		self.__server = server.as_basic_server_interface()
		self.__logger = self.__server.logger
		self.__plugin = plugin

	@property
	def is_player(self) -> bool:
		return False

	@property
	def is_console(self) -> bool:
		return False

	def get_server(self) -> 'ServerInterface':
		return self.__server

	def get_permission_level(self) -> int:
		return PermissionLevel.PLUGIN_LEVEL

	def reply(self, message: Any, **kwargs) -> None:
		misc_util.print_text_to_console(self.__logger, message)

	def __str__(self):
		return 'Plugin' if self.__plugin is None else 'Plugin {}'.format(self.__plugin)

	def __repr__(self):
		return '{}[plugin={}]'.format(type(self).__name__, self.__plugin)
