import functools
from threading import Thread
from typing import Callable, List, TYPE_CHECKING, Optional

from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin


ServerControlFunction = Callable[[], bool]


class ServerCommand(SubCommand):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)
		self.restart_thread: Optional[Thread] = None

	@override
	def get_command_node(self) -> Literal:
		node = (
			self.owner_command_root('server').
			runs(lambda src: self.reply_help_message(src, 'mcdr_command.help_message.server'))
		)
		functions: List[ServerControlFunction] = [
			self.server_interface.start,
			self.server_interface.stop,
			self.server_interface.stop_exit,
			self.server_interface.exit,
			self.server_interface.restart,
			self.server_interface.kill,
		]

		for func in functions:
			func_name = func.__name__
			node.then(Literal(func_name).runs(lambda src, ctx, f=func, fn=func_name: self.__common_operation(src, f, fn)))

		return node

	def __common_operation(self, source: CommandSource, func: ServerControlFunction, func_name: str):
		def do_operation(in_thread: bool):
			try:
				ok = func()
				assert type(ok) is bool, 'Function {} should return bool, but found {}'.format(func_name, type(ok))
				if ok:
					source.reply(self.tr('mcdr_command.server.{}.success'.format(func_name)))
				else:
					source.reply(self.tr('mcdr_command.server.{}.failed'.format(func_name)))
					if not source.is_console:
						source.reply(self.tr('mcdr_command.server.see_console'))
			finally:
				if in_thread:
					self.restart_thread = None

		if func == self.server_interface.restart:
			if self.restart_thread is not None:
				source.reply(self.tr('mcdr_command.server.{}.spam'.format(func_name)))
				return
			self.restart_thread = Thread(target=functools.partial(do_operation, True), name='ServerRestart', daemon=True)
			self.restart_thread.start()
		else:
			do_operation(False)
