class IllegalNodeOperation(Exception):
	pass


class CommandError(Exception):
	def __init__(self, message, fail_position_hint):
		self.message = message
		self.fail_position_hint = fail_position_hint

	def __str__(self):
		return '{}: {}'.format(self.message, self.fail_position_hint)


class UnknownCommand(CommandError):
	"""
	When the command finishes parsing, but current node doesn't have a callback function
	"""
	def __init__(self, fail_position):
		super().__init__('Unknown Command', fail_position)


class UnknownArgument(CommandError):
	"""
	When there's remaining command string, but there's no matched Literal nodes and no general argument nodes
	"""
	def __init__(self, fail_position):
		super().__init__('Unknown Argument', fail_position)


class UnknownRootArgument(UnknownArgument):
	"""
	The same as UnknownArgument, but it fails to match at root node
	"""
	pass


class PermissionDenied(CommandError):
	"""
	The command source is not allowed to executes inside this command tree
	"""
	def __init__(self, fail_position):
		super().__init__('Permission denied', fail_position)


class CommandSyntaxError(CommandError):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	def __init__(self, message, char_read):
		super().__init__(message, 'unknown')
		self.message = message
		self.char_read = char_read

	def set_fail_position_hint(self, fail_position_hint):
		self.fail_position_hint = fail_position_hint


class IllegalArgument(CommandSyntaxError):
	"""
	General illegal argument error
	Used in integer parsing failure etc.
	"""
	pass


class IllegalLiteralArgument(CommandSyntaxError):
	"""
	Used by Literal node parsing failure for fail-soft
	"""
	pass


class NumberOutOfRange(CommandSyntaxError):
	"""
	The parsed number value is out of the restriction range
	"""
	pass


class EmptyText(CommandSyntaxError):
	"""
	The text is empty, and it's not allowed to be
	"""
	pass
