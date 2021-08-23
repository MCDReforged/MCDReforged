from mcdreforged.command.builder.exception import UnknownArgument
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand


class ReloadCommand(SubCommand):
	def get_command_node(self) -> Literal:
		return (
			self.control_command_root({'r', 'reload'}).
			runs(lambda src: src.reply(self.get_help_message(src, 'mcdr_command.help_message.reload'))).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
			then(Literal({'plugin', 'plg'}).runs(self.refresh_changed_plugins)).
			then(Literal({'config', 'cfg'}).runs(self.reload_config)).
			then(Literal({'permission', 'perm'}).runs(self.reload_permission)).
			then(Literal('all').runs(self.reload_all))
		)

	def refresh_changed_plugins(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', log_success=False)
		self._print_plugin_operation_result_if_no_error(source, ret)

	def reload_config(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.load_config, 'reload_config')

	def reload_permission(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.permission_manager.load_permission_file, 'reload_permission')

	def reload_all(self, source: CommandSource):
		self.reload_config(source)
		self.reload_permission(source)
		self.refresh_changed_plugins(source)
