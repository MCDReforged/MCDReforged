from typing import TYPE_CHECKING, Callable, Any

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin


class AbortSubCommand(SubCommand):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin', abort_callback: Callable[[CommandSource], Any]):
		super().__init__(mcdr_plugin)
		self.abort_callback = abort_callback

	def get_command_node(self) -> Literal:
		return self.control_command_root('abort').runs(self.abort_callback)
