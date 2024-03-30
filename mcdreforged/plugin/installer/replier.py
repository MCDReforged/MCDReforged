import typing
from abc import ABC, abstractmethod

from mcdreforged.constants import core_constant
from mcdreforged.utils.types.message import MessageText

if typing.TYPE_CHECKING:
	from mcdreforged.command.command_source import CommandSource


class Replier(ABC):
	DEFAULT_LANGUAGE = core_constant.DEFAULT_LANGUAGE

	@property
	def language(self) -> str:
		return self.DEFAULT_LANGUAGE

	@abstractmethod
	def reply(self, message: MessageText):
		raise NotImplementedError()


class NoopReplier(Replier):
	def reply(self, message: MessageText):
		pass


class StdoutReplier(Replier):
	def reply(self, message: MessageText):
		from mcdreforged.minecraft.rtext.text import RTextBase
		if isinstance(message, RTextBase):
			message = message.to_colored_text()
		print(message)


class CommandSourceReplier(Replier):
	def __init__(self, command_source: 'CommandSource'):
		self.command_source = command_source

	@property
	def language(self) -> str:
		return self.command_source.get_preference().language

	def reply(self, message: MessageText):
		self.command_source.reply(message)
