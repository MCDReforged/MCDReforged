from abc import ABC
from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional

from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_util
from mcdreforged.utils.types import MessageText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.info_reactor.info import Info
	from mcdreforged.plugin.server_interface import ServerInterface
	from mcdreforged.plugin.type.plugin import AbstractPlugin
	from mcdreforged.preference.preference_manager import PreferenceItem


class CommandSource(ABC):
	"""
	:class:`CommandSource`: is an abstracted command executor model. It provides several methods for command execution

	Class inheriting tree::

		CommandSource
		├── InfoCommandSource
		│   ├── PlayerCommandSource
		│   └── ConsoleCommandSource
		└── PluginCommandSource

	Plugins can declare a class inherited from :class:`CommandSource` to create their own command source
	"""

	@property
	def is_player(self) -> bool:
		"""
		If the command source is a player command source

		:return: ``True`` if it's a player command source, ``False`` otherwise
		"""
		raise NotImplementedError()

	@property
	def is_console(self) -> bool:
		"""
		If the command source is a console command source

		:return: ``True`` if it's a console command source, ``False`` otherwise
		"""
		raise NotImplementedError()

	def get_server(self) -> 'ServerInterface':
		"""
		Return the server interface instance
		"""
		raise NotImplementedError()

	def get_permission_level(self) -> int:
		"""
		Return the permission level that the command source has

		The permission level is represented by int
		"""
		raise NotImplementedError()

	def get_preference(self) -> Optional['PreferenceItem']:
		"""
		Return the preference of the command source

		Only :class:`PlayerCommandSource` and :class:`ConsoleCommandSource` are supported, otherwise None will be returned

		.. seealso::

			:class:`~mcdreforged.plugin.server_interface.ServerInterface`'s method :meth:`~mcdreforged.plugin.server_interface.ServerInterface.get_preference`

		.. versionadded:: v2.1.0
		"""
		return None

	@contextmanager
	def preferred_language_context(self):
		"""
		A quick helper method to use the language value in preference to create a context
		with :meth:`RTextMCDRTranslation.language_context() <mcdreforged.translation.translation_text.RTextMCDRTranslation.language_context>`

		.. seealso::

			Class :class:`~mcdreforged.translation.translation_text.RTextMCDRTranslation`

		Example usage::

			with source.preferred_language_context():
				message = source.get_server().rtr('my_plugin.placeholder').to_plain_text()
				text.set_click_event(RAction.suggest_command, message)

		.. versionadded:: v2.1.0
		"""
		with RTextMCDRTranslation.language_context(self.get_preference().language):
			yield

	def has_permission(self, level: int) -> bool:
		"""
		A helper method for testing permission requirement

		:param level: The permission level to be tested
		:return: If the command source has not less permission level than the given permission level
		"""
		return self.get_permission_level() >= level

	def has_permission_higher_than(self, level: int) -> bool:
		"""
		Just like the :meth:`CommandSource.has_permission`, but this time it is a greater than judgment

		:param level: The permission level to be tested
		:return: If the command source has greater permission level than the given permission level
		"""
		return self.get_permission_level() > level

	def reply(self, message: MessageText, **kwargs) -> None:
		"""
		Send a message to the command source. The message can be anything including RTexts

		:param message: The message you want to send
		:keyword encoding: The encoding method for the message. It's only used in :class:`PlayerCommandSource`
		:keyword console_text: Message override when it's a :class:`ConsoleCommandSource`
		"""
		raise NotImplementedError()


class InfoCommandSource(CommandSource, ABC):
	"""
	Command source originated from an info created by MCDR
	"""
	def __init__(self, mcdr_server: 'MCDReforgedServer', info: 'Info'):
		self._mcdr_server = mcdr_server
		self.__info = info

	def get_info(self) -> 'Info':
		"""
		Return the Info instance that this command source is created from
		"""
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

		self.player: str = player
		"""The name of the player"""

	@property
	def is_player(self) -> bool:
		return True

	@property
	def is_console(self) -> bool:
		return False

	def get_preference(self) -> Optional['PreferenceItem']:
		return self.get_server().get_preference(self)

	def reply(self, message: MessageText, *, encoding: Optional[str] = None, **kwargs):
		"""
		:keyword encoding: encoding method to be used in :meth:`ServerInterface.tell`
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

	def get_preference(self) -> Optional['PreferenceItem']:
		return self.get_server().get_preference(self)

	def reply(self, message: MessageText, *, console_text: Optional[MessageText] = None, **kwargs):
		"""
		:keyword console_text: If it's specified, overwrite the value of parameter ``message`` with it
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

	def reply(self, message: MessageText, **kwargs) -> None:
		misc_util.print_text_to_console(self.__logger, message)

	def __str__(self):
		return 'Plugin' if self.__plugin is None else 'Plugin {}'.format(self.__plugin)

	def __repr__(self):
		return '{}[plugin={}]'.format(type(self).__name__, self.__plugin)
