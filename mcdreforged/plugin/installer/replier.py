import abc
import typing

from mcdreforged.utils.types import MessageText

if typing.TYPE_CHECKING:
	from mcdreforged.command.command_source import CommandSource


class Replier(abc.ABC):
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

	def reply(self, message: MessageText):
		self.command_source.reply(message)
