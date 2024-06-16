import typing
from abc import ABC, abstractmethod

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.utils.types.message import MessageText

if typing.TYPE_CHECKING:
	from mcdreforged.command.command_source import CommandSource


class Replier(ABC):
	@property
	def language(self) -> str:
		return core_constant.DEFAULT_LANGUAGE

	@abstractmethod
	def is_console(self) -> bool:
		raise NotImplementedError()

	@abstractmethod
	def reply(self, message: MessageText) -> None:
		raise NotImplementedError()

	@property
	def padding_width(self) -> int:
		return 0


class NoopReplier(Replier):
	@override
	def is_console(self) -> bool:
		return False

	@override
	def reply(self, message: MessageText):
		pass


class StdoutReplier(Replier):
	@override
	def is_console(self) -> bool:
		return True

	@override
	def reply(self, message: MessageText):
		from mcdreforged.minecraft.rtext.text import RTextBase
		if isinstance(message, RTextBase):
			message = message.to_colored_text()
		print(message)


class CommandSourceReplier(Replier):
	def __init__(self, command_source: 'CommandSource'):
		self.command_source = command_source

	@property
	@override
	def language(self) -> str:
		return self.command_source.get_preference().language

	@override
	def is_console(self) -> bool:
		return self.command_source.is_console

	@override
	def reply(self, message: MessageText):
		self.command_source.reply(message)

	@property
	def padding_width(self) -> int:
		if self.command_source.is_console:
			return len('[MCDR] [00:00:00] [PIM/INFO]: ')
		else:
			return 0
