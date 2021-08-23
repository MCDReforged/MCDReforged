import threading

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RText, RColor, RAction, RStyle
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand


class StatusCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			self.public_command_root('status').runs(self.print_mcdr_status)
		)

	def print_mcdr_status(self, source: CommandSource):
		def bool_formatter(bl: bool) -> RText:
			return RText(bl, RColor.green if bl else RColor.red)
		rcon_status_dict = {
			True: self.tr('mcdr_command.print_mcdr_status.online'),
			False: self.tr('mcdr_command.print_mcdr_status.offline')
		}

		source.reply(
			RText(self.tr('mcdr_command.print_mcdr_status.line1', core_constant.NAME, core_constant.VERSION)).
			c(RAction.open_url, core_constant.GITHUB_URL).
			h(RText(core_constant.GITHUB_URL, styles=RStyle.underlined, color=RColor.blue))
		)

		if not source.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL):
			return
		source.reply(RText.join('\n', [
			RText(self.tr('mcdr_command.print_mcdr_status.line2', self.tr(self.mcdr_server.mcdr_state.value))),
			RText(self.tr('mcdr_command.print_mcdr_status.line3', self.tr(self.mcdr_server.server_state.value))),
			RText(self.tr('mcdr_command.print_mcdr_status.line4', bool_formatter(self.mcdr_server.is_server_startup()))),
			RText(self.tr('mcdr_command.print_mcdr_status.line5', bool_formatter(self.mcdr_server.should_exit_after_stop()))),
			RText(self.tr('mcdr_command.print_mcdr_status.line6', rcon_status_dict[self.server_interface.is_rcon_running()])),
			RText(self.tr('mcdr_command.print_mcdr_status.line7', self.mcdr_server.plugin_manager.get_plugin_amount())).c(RAction.suggest_command, '!!MCDR plugin list')
		]))

		if not source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
			return
		source.reply(RText.join('\n', [
			self.tr('mcdr_command.print_mcdr_status.extra_line1', self.mcdr_server.process.pid if self.mcdr_server.process is not None else '§rN/A§r'),
			self.tr('mcdr_command.print_mcdr_status.extra_line2', self.mcdr_server.task_executor.task_queue.qsize(), core_constant.MAX_TASK_QUEUE_SIZE),
			self.tr('mcdr_command.print_mcdr_status.extra_line3', threading.active_count())
		]))
		for thread in threading.enumerate():
			source.reply('  §r-§r {}'.format(thread.getName()))
