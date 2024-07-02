from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import TYPE_CHECKING, Optional

from typing_extensions import override

from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import misc_utils, class_utils
from mcdreforged.utils.exception import IllegalCallError
from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.info_reactor.info import Info
	from mcdreforged.plugin.si.server_interface import ServerInterface
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
		return isinstance(self, PlayerCommandSource)

	@property
	def is_console(self) -> bool:
		"""
		If the command source is a console command source

		:return: ``True`` if it's a console command source, ``False`` otherwise
		"""
		return isinstance(self, ConsoleCommandSource)

	@abstractmethod
	def get_server(self) -> 'ServerInterface':
		"""
		Return the server interface instance
		"""
		raise NotImplementedError()

	@abstractmethod
	def get_permission_level(self) -> int:
		"""
		Return the permission level that the command source has

		The permission level is represented by int
		"""
		raise NotImplementedError()

	def get_preference(self) -> 'PreferenceItem':
		"""
		Return the preference of the command source

		By default, the default preference of MCDR from
		:meth:`ServerInterface.get_default_preference() <mcdreforged.plugin.si.server_interface.ServerInterface.get_preference>`
		will be returned

		Subclasses might override this method to return customized preference.
		e.g. :class:`PlayerCommandSource` will return the preference of the corresponding player

		.. seealso::

			method :meth:`ServerInterface.get_preference() <mcdreforged.plugin.si.server_interface.ServerInterface.get_preference>`

		.. versionadded:: v2.1.0
		"""
		from mcdreforged.plugin.si.server_interface import ServerInterface
		server = ServerInterface.get_instance()
		if server is None:
			raise IllegalCallError('Cannot get default preference when MCDR is not running')
		return server.get_default_preference()

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

	@abstractmethod
	def reply(self, message: MessageText, **kwargs) -> None:
		"""
		Send a message to the command source. The message can be anything including RTexts

		:param message: The message you want to send
		:keyword encoding: The encoding method for the message. It's only used in :class:`PlayerCommandSource`
		:keyword console_text: Message override when it's a :class:`ConsoleCommandSource`
		"""
		raise NotImplementedError()

	def __eq__(self, other) -> bool:
		"""
		.. versionadded:: v2.12.2

			All MCDR builtin command sources have the implemented the `__eq__` method
		"""
		return super().__eq__(other)


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

	@override
	def get_server(self) -> 'ServerInterface':
		return self._mcdr_server.basic_server_interface

	@override
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

	@override
	def get_preference(self) -> 'PreferenceItem':
		return self.get_server().get_preference(self)

	@override
	def reply(self, message: MessageText, *, encoding: Optional[str] = None, **kwargs):
		"""
		:keyword encoding: encoding method to be used in :meth:`ServerInterface.tell`
		"""
		self._mcdr_server.basic_server_interface.tell(self.player, message, encoding=encoding)

	def __eq__(self, other) -> bool:
		return isinstance(other, PlayerCommandSource) and self.player == other.player

	def __str__(self):
		return 'Player {}'.format(self.player)

	def __repr__(self):
		return class_utils.represent(self, {
			'player': self.player,
			'info_id': self.get_info().id,
		})


class ConsoleCommandSource(InfoCommandSource):
	def __init__(self, mcdr_server, info):
		if not info.is_from_console:
			raise TypeError('{} should be built from console info'.format(self.__class__.__name__))
		super().__init__(mcdr_server, info)

	@override
	def get_preference(self) -> 'PreferenceItem':
		return self.get_server().get_preference(self)

	@override
	def reply(self, message: MessageText, *, console_text: Optional[MessageText] = None, **kwargs):
		"""
		:keyword console_text: If it's specified, overwrite the value of parameter ``message`` with it
		"""
		if console_text is not None:
			message = console_text
		with self.preferred_language_context():
			misc_utils.print_text_to_console(self._mcdr_server.logger, message)

	def __eq__(self, other) -> bool:
		return isinstance(other, ConsoleCommandSource)

	def __str__(self):
		return 'Console'

	def __repr__(self):
		return class_utils.represent(self, {
			'info_id': self.get_info().id,
		})


class PluginCommandSource(CommandSource):
	def __init__(self, server: 'ServerInterface', plugin: Optional['AbstractPlugin'] = None):
		self.__server = server.as_basic_server_interface()
		self.__logger = self.__server.logger
		self.__plugin = plugin

	@override
	def get_server(self) -> 'ServerInterface':
		return self.__server

	@override
	def get_permission_level(self) -> int:
		return PermissionLevel.PLUGIN_LEVEL

	@override
	def reply(self, message: MessageText, **kwargs) -> None:
		misc_utils.print_text_to_console(self.__logger, message)

	def __eq__(self, other) -> bool:
		return isinstance(other, PluginCommandSource) and self.__plugin.get_id() == other.__plugin.get_id()

	def __str__(self):
		return 'Plugin' if self.__plugin is None else 'Plugin {}'.format(self.__plugin)

	def __repr__(self):
		return class_utils.represent(self, {
			'plugin': self.__plugin,
		})
