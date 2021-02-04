from abc import ABC
from typing import Optional


class CommandErrorBase(Exception, ABC):
	pass


class IllegalNodeOperation(CommandErrorBase):
	"""
	This node is not allowed to do this
	"""
	pass


class CommandError(CommandErrorBase, ABC):
	"""
	The basic error, for errors raising when a command source is executing a command
	"""
	def __init__(self, message: str, parsed_command: str, failed_command: str):
		self.__message = message
		self._parsed_command = parsed_command
		self._failed_command = failed_command
		self.__handled = False

	def __str__(self):
		return '{}: {}<--'.format(self.__message, self._failed_command)

	def to_mc_color_text(self):
		return '§c{}: §r{}§c{}§4<--'.format(self.__message, self._parsed_command, self._failed_command[len(self._parsed_command):])

	def get_error_data(self) -> tuple:
		return ()

	def set_message(self, message: str):
		self.__message = message

	def get_parsed_command(self) -> str:
		return self._parsed_command

	def get_failed_command(self) -> str:
		return self._failed_command

	def set_handled(self) -> None:
		"""
		It won't make any difference to the command node tree execution
		But it might be useful for outer error handlers
		"""
		self.__handled = True

	def is_handled(self) -> bool:
		return self.__handled


class UnknownCommand(CommandError):
	"""
	When the command finishes parsing, but current node doesn't have a callback function
	"""
	def __init__(self, parsed_command, failed_command):
		super().__init__('Unknown Command', parsed_command, failed_command)


class UnknownArgument(CommandError):
	"""
	When there's remaining command string, but there's no matched Literal nodes and no general argument nodes
	"""
	def __init__(self, parsed_command: str, failed_command: str):
		super().__init__('Unknown Argument', parsed_command, failed_command)


class UnknownRootArgument(UnknownArgument):
	"""
	The same as UnknownArgument, but it fails to match at root node
	"""
	pass


class RequirementNotMet(CommandError):
	"""
	The specified requirement for the command source to enter this node is not met
	"""
	DEFAULT_REASON = object()

	def __init__(self, parsed_command: str, failed_command: str, reason: Optional[str]):
		self.__reason = reason if reason is not None else self.DEFAULT_REASON
		super().__init__(self.__reason, parsed_command, failed_command)

	def get_reason(self) -> Optional[str]:
		return self.__reason

	def get_error_data(self) -> tuple:
		return (self.get_reason(),)

# -----------------
#   Syntax things
# -----------------


class CommandSyntaxError(CommandError, ABC):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	def __init__(self, message: str, char_read: int):
		super().__init__(message, '?', '?')
		self.message = message
		self.char_read = char_read

	def set_parsed_command(self, parsed_command):
		self._parsed_command = parsed_command

	def set_failed_command(self, failed_command):
		self._failed_command = failed_command


class IllegalArgument(CommandSyntaxError, ABC):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	pass


class LiteralNotMatch(CommandSyntaxError):
	"""
	Used by Literal node parsing failure for fail-soft
	"""
	pass


class AbstractOutOfRange(IllegalArgument, ABC):
	def __init__(self, message: str, char_read: int, value, range_l, range_r):
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
	def _get_boundary_text(cls, value) -> str:
		return str(value) if value is not None else '/'

	def get_error_data(self) -> tuple:
		return self.__value, self._get_boundary_text(self.__range_l), self._get_boundary_text(self.__range_r)


# Number things


class NumberOutOfRange(AbstractOutOfRange):
	"""
	The parsed number value is out of the restriction range
	"""
	def __init__(self, char_read: int, value, range_l, range_r):
		super().__init__('Value out of range [{}, {}]'.format(self._get_boundary_text(range_l), self._get_boundary_text(range_r)), char_read, value, range_l, range_r)


class InvalidNumber(IllegalArgument):
	def __init__(self, char_read: int):
		super().__init__('Invalid number', char_read)


class InvalidInteger(IllegalArgument):
	def __init__(self, char_read: int):
		super().__init__('Invalid integer', char_read)


class InvalidFloat(IllegalArgument):
	def __init__(self, char_read: int):
		super().__init__('Invalid float', char_read)


# Text things


class TextLengthOutOfRange(AbstractOutOfRange):
	"""
	The length of the given text is out of the restriction range
	"""
	def __init__(self, char_read: int, value, range_l, range_r):
		super().__init__('Text length {} out of range [{}, {}]'.format(value, self._get_boundary_text(range_l), self._get_boundary_text(range_r)), char_read, value, range_l, range_r)


class IllegalEscapesUsage(IllegalArgument):
	"""
	The text is empty, and it's not allowed to be
	"""
	def __init__(self, char_read: int):
		super().__init__('Illegal usage of escapes', char_read)


class UnclosedQuotedString(IllegalArgument):
	"""
	The text is empty, and it's not allowed to be
	"""
	def __init__(self, char_read: int):
		super().__init__('Unclosed quoted string', char_read)


class EmptyText(IllegalArgument):
	"""
	The text is empty, and it's not allowed to be
	"""
	def __init__(self, char_read: int):
		super().__init__('Empty text is not allowed', char_read)
