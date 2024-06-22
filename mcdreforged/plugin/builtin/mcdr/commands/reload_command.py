from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand


class ReloadCommand(SubCommand):
	@override
	def get_command_node(self) -> Literal:
		return (
			self.control_command_root({'r', 'reload'}).
			runs(lambda src: self.reply_help_message(src, 'mcdr_command.help_message.reload')).
			then(Literal({'plugin', 'plg'}).runs(self.refresh_changed_plugins)).
			then(Literal({'config', 'cfg'}).runs(self.reload_config)).
			then(Literal({'permission', 'perm'}).runs(self.reload_permission)).
			then(Literal('all').runs(self.reload_all))
		)

	def refresh_changed_plugins(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_changed_plugins, 'refresh_changed_plugins', reply_success=False)
		self._print_plugin_operation_result_if_no_error(source, ret)

	def reload_config(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.load_config, 'reload_config')

	def reload_permission(self, source: CommandSource):
		self.function_call(source, self.mcdr_server.permission_manager.load_permission_file, 'reload_permission')

	def reload_all(self, source: CommandSource):
		self.reload_config(source)
		self.reload_permission(source)
		self.refresh_changed_plugins(source)
