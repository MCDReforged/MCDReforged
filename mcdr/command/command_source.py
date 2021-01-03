from mcdr.utils import misc_util


class CommandSourceType:
	PLAYER = 0
	CONSOLE = 1


class CommandSource:
	source_type: int

	def __init__(self, mcdr_server, source_type):
		self._mcdr_server = mcdr_server
		self.source_type = source_type

	@property
	def is_player(self) -> bool:
		raise NotImplementedError()

	def get_permission_level(self) -> int:
		return self._mcdr_server.permission_manager.get_permission(self)

	def has_permission(self, level: int) -> bool:
		return self.get_permission_level() >= level

	def has_permission_higher_than(self, level: int) -> bool:
		return self.get_permission_level() > level

	def reply(self, message, **kwargs):
		"""
		Reply to the command source
		:param message: The message you want to send. It will be mapped with str() unless it's a RTextBase
		"""
		raise NotImplementedError()

	def __str__(self):
		raise NotImplementedError()


class PlayerCommandSource(CommandSource):
	def __init__(self, mcdr_server, player: str):
		super().__init__(mcdr_server, CommandSourceType.PLAYER)
		self.player = player

	@property
	def is_player(self):
		return True

	def reply(self, message, **kwargs):
		"""
		Specify key word argument encoding
		"""
		self._mcdr_server.server_interface.tell(self.player, message, encoding=kwargs.get('encoding'), is_plugin_call=False)

	def __str__(self):
		return 'Player {}'.format(self.player)


class ConsoleCommandSource(CommandSource):
	def __init__(self, mcdr_server):
		super().__init__(mcdr_server, CommandSourceType.CONSOLE)

	@property
	def is_player(self):
		return False

	def reply(self, message, **kwargs):
		misc_util.print_text_to_console(self._mcdr_server.logger, message)

	def __str__(self):
		return 'Console'
