from typing import TYPE_CHECKING, Callable, Any

from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin


class ConfirmSubCommand(SubCommand):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin', confirm_callback: Callable[[CommandSource], Any]):
		super().__init__(mcdr_plugin)
		self.confirm_callback = confirm_callback

	@override
	def get_command_node(self) -> Literal:
		return self.control_command_root('confirm').runs(self.confirm_callback)
