from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand


class CheckUpdateCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			self.control_command_root({'checkupdate', 'cu'}).
			runs(lambda src: self.mcdr_server.update_helper.check_update(condition_check=lambda: True, reply_func=src.reply))
		)
