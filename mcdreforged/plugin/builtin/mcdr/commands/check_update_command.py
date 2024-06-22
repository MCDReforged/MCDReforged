from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand


class CheckUpdateCommand(SubCommand):
	@override
	def get_command_node(self) -> Literal:
		return (
			self.control_command_root({'checkupdate', 'cu'}).
			runs(self.__check_update)
		)

	def __check_update(self, source: CommandSource):
		self.mcdr_server.update_helper.check_update(condition_check=lambda: True, reply_func=source.reply)
