from abc import ABC
from typing import Optional, Union

from mcdreforged.minecraft.rtext.text import RTextBase, RText, RColor
from mcdreforged.utils.types import MessageText


class CommandErrorBase(Exception, ABC):
	"""
	The base exception class for all command related errors

	Class inheriting tree::
	
		CommandErrorBase
		├── IllegalNodeOperation
		└── CommandError
			├── UnknownCommand
			├── UnknownArgument
			├── RequirementNotMet
			└── CommandSyntaxError
				└── IllegalArgument
					├── AbstractOutOfRange
					│   ├── NumberOutOfRange
					│   └── TextLengthOutOfRange
					├── InvalidNumber
					├── InvalidInteger
					├── InvalidFloat
					├── IllegalEscapesUsage
					├── UnclosedQuotedString
					├── EmptyText
					├── InvalidBoolean
					└── InvalidEnumeration
	"""
	pass


class IllegalNodeOperation(CommandErrorBase):
	"""
	The operation is unsupported by this node
	"""
	pass


class CommandError(CommandErrorBase, ABC):
	"""
	The basic exception, for errors raised when parsing a command
	"""
	def __init__(self, message: MessageText, parsed_command: str, failed_command: str):
		#  !!something wroooong command
		#  [--parsed--|-error-]
		#  [------failed------]

		self.__message: MessageText = message
		self._parsed_command: str = parsed_command
		self._failed_command: str = failed_command
		self.__handled: bool = False

	def __str__(self):
		return '{}: {}<--'.format(self.__message, self._failed_command)

	def to_rtext(self) -> RTextBase:
		return RTextBase.format(
			'{}: {}{}{}',
			RTextBase.from_any(self.__message).copy().set_color(RColor.red),
			RText(self.get_parsed_command(), RColor.dark_red),
			RText(self.get_error_segment(), RColor.red),
			RText('<--', RColor.dark_red)
		)

	def get_error_data(self) -> tuple:
		"""
		Data that might be helpful for error report

		It will be used in error message str formatting
		"""
		return ()

	def set_message(self, message: str):
		self.__message = message

	def get_parsed_command(self) -> str:
		"""
		:return: A prefix of the input command that has been successfully parsed
		"""
		return self._parsed_command

	def get_failed_command(self) -> str:
		"""
		:return: A prefix of the input command that is parsing when the failure occurs
		"""
		return self._failed_command

	def get_error_segment(self) -> str:
		"""
		:return: The command segment that causes the error
		"""
		return self._failed_command[len(self._parsed_command):]

	def set_handled(self) -> None:
		"""
		When handling the command error by error listener on the command tree node, you can use this method to tell MCDR the command error has been handled
		so MCDR will not display the default command failure message to the command source like ``Unknown argument: !!MCDR reload this<--``

		It won't make any difference to the command node tree execution, but it might be useful for outer error handlers
		"""
		self.__handled = True

	def is_handled(self) -> bool:
		return self.__handled


class UnknownCommand(CommandError):
	"""
	When the command finishes parsing, but current node doesn't have a command callback function
	"""
	def __init__(self, parsed_command, failed_command):
		super().__init__('Unknown Command', parsed_command, failed_command)


class UnknownArgument(CommandError):
	"""
	When there's remaining command string, but there's no matched children command nodes
	"""
	def __init__(self, parsed_command: str, failed_command: str):
		super().__init__('Unknown Argument', parsed_command, failed_command)


class UnknownRootArgument(UnknownArgument):
	"""
	The same as :class:`UnknownArgument`, but it fails to match at root node

	Internal-use only

	:meta private:
	"""
	pass


class RequirementNotMet(CommandError):
	"""
	The specified requirement for the command source to enter this node is not met
	"""
	__NO_REASON = RText('Requirement not met')

	def __init__(self, parsed_command: str, failed_command: str, reason: Optional[MessageText]):
		self.__reason: MessageText = reason if reason is not None else self.__NO_REASON
		super().__init__(self.__reason, parsed_command, failed_command)

	def has_custom_reason(self) -> bool:
		return self.__reason is not self.__NO_REASON

	def get_reason(self) -> MessageText:
		return self.__reason

	def get_error_data(self) -> tuple:
		return (self.get_reason(),)

# -----------------
#   Syntax things
# -----------------


class CommandSyntaxError(CommandError, ABC):
	"""
	The basic exception for command parsing error
	"""
	def __init__(self, message: str, char_read: Union[int, str]):
		super().__init__(message, '', '?' if isinstance(char_read, int) else char_read)
		self.message = message
		self.char_read = char_read if isinstance(char_read, int) else len(char_read)

	def set_parsed_command(self, parsed_command):
		self._parsed_command = parsed_command

	def set_failed_command(self, failed_command):
		self._failed_command = failed_command


class IllegalArgument(CommandSyntaxError, ABC):
	"""
	The basic exception for argument parsing error, usually caused by wrong argument syntax
	"""
	pass


class LiteralNotMatch(CommandSyntaxError):
	"""
	Used by Literal node parsing failure for fail-soft

	Internal-use only

	:meta private:
	"""
	pass


class AbstractOutOfRange(IllegalArgument, ABC):
	"""
	The basic exception for out-of-range like argument parsing error
	"""
	def __init__(self, message: str, char_read: Union[int, str], value, range_l, range_r):
		"""
		:param value: The actual value
		:param range_l: The left boundary
		:param range_r: The right boundary
		"""
		super().__init__(message, char_read)
		self.__value = value
		self.__range_l = range_l
		self.__range_r = range_r

	@classmethod
	def get_boundary_text(cls, value) -> str:
		return str(value) if value is not None else '/'

	def get_error_data(self) -> tuple:
		return self.__value, self.get_boundary_text(self.__range_l), self.get_boundary_text(self.__range_r)


# Number things


class NumberOutOfRange(AbstractOutOfRange):
	"""
	The parsed number value is out of the restriction range
	"""
	def __init__(self, char_read: Union[int, str], value, range_l, range_r):
		super().__init__('Value out of range [{}, {}]'.format(self.get_boundary_text(range_l), self.get_boundary_text(range_r)), char_read, value, range_l, range_r)


class InvalidNumber(IllegalArgument):
	"""
	The parsed value is not a valid number
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Invalid number', char_read)


class InvalidInteger(IllegalArgument):
	"""
	The parsed value is not a valid integer
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Invalid integer', char_read)


class InvalidFloat(IllegalArgument):
	"""
	The parsed value is not a valid float
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Invalid float', char_read)


# Text things


class TextLengthOutOfRange(AbstractOutOfRange):
	"""
	The length of the given text is out of the restriction range
	"""
	def __init__(self, char_read: Union[int, str], value, range_l, range_r):
		super().__init__('Text length {} out of range [{}, {}]'.format(value, self.get_boundary_text(range_l), self.get_boundary_text(range_r)), char_read, value, range_l, range_r)


class IllegalEscapesUsage(IllegalArgument):
	"""
	The text contains illegal ``\\`` usage
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Illegal usage of escapes', char_read)


class UnclosedQuotedString(IllegalArgument):
	"""
	The quote is unclosed
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Unclosed quoted string', char_read)


class EmptyText(IllegalArgument):
	"""
	The text is empty, which is not allowed
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Empty text is not allowed', char_read)


# Other Arguments


class InvalidBoolean(IllegalArgument):
	"""
	The parsed value is not a valid boolean
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Invalid boolean', char_read)


class InvalidEnumeration(IllegalArgument):
	"""
	The parsed value is not a valid Enum
	"""
	def __init__(self, char_read: Union[int, str]):
		super().__init__('Invalid enumeration', char_read)
