import threading
from typing import List

import psutil
from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants import core_constant
from mcdreforged.executor.task_executor_queue import TaskPriority
from mcdreforged.minecraft.rtext.click_event import RAction
from mcdreforged.minecraft.rtext.style import RColor, RStyle
from mcdreforged.minecraft.rtext.text import RText
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand
from mcdreforged.utils import tree_printer


class StatusCommand(SubCommand):
	@override
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
			self.tr('mcdr_command.print_mcdr_status.line1', core_constant.NAME, core_constant.VERSION).
			c(RAction.open_url, core_constant.GITHUB_URL).
			h(RText(core_constant.GITHUB_URL, styles=RStyle.underlined, color=RColor.blue))
		)

		if not source.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL):
			return
		for line in [
			self.tr('mcdr_command.print_mcdr_status.line2', self.tr(self.mcdr_server.mcdr_state.value)),
			self.tr('mcdr_command.print_mcdr_status.line3', self.tr(self.mcdr_server.server_state.value)),
			self.tr('mcdr_command.print_mcdr_status.line4', bool_formatter(self.mcdr_server.is_server_startup())),
			self.tr('mcdr_command.print_mcdr_status.line5', bool_formatter(self.mcdr_server.should_exit_after_stop())),
			self.tr('mcdr_command.print_mcdr_status.line6', rcon_status_dict[self.server_interface.is_rcon_running()]),
			self.tr('mcdr_command.print_mcdr_status.line7', self.mcdr_server.plugin_manager.get_plugin_amount()).c(RAction.suggest_command, '!!MCDR plugin list')
		]:
			source.reply(line)

		# ------------ Physical server secrets ------------
		if not source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
			return

		process_pid = self.mcdr_server.process_manager.get_pid()
		source.reply(self.tr('mcdr_command.print_mcdr_status.extra.pid', process_pid if process_pid is not None else RText('N/A', RColor.gray)))
		if process_pid is not None and self.mcdr_server.process_manager.is_alive():
			def children_getter(proc: psutil.Process) -> List[psutil.Process]:
				return proc.children()

			def name_getter(proc: psutil.Process) -> str:
				return '{}: {}'.format(proc.name(), proc.pid)

			def line_writer(line_: str):
				source.reply('  ' + line_)
			try:
				tree_printer.print_tree(
					psutil.Process(process_pid),
					children_getter,
					name_getter,
					line_writer
				)
			except psutil.NoSuchProcess as e:
				self.mcdr_server.logger.error('Fail to fetch process tree from pid {}: {}'.format(process_pid, e))

		qsizes = self.mcdr_server.task_executor.get_queue_sizes()
		source.reply(self.tr('mcdr_command.print_mcdr_status.extra.queue_info', qsizes[TaskPriority.INFO], core_constant.MAX_TASK_QUEUE_SIZE_INFO))
		source.reply(self.tr('mcdr_command.print_mcdr_status.extra.queue_regular', qsizes[TaskPriority.REGULAR], core_constant.MAX_TASK_QUEUE_SIZE_REGULAR))
		source.reply(self.tr('mcdr_command.print_mcdr_status.extra.thread', threading.active_count()))
