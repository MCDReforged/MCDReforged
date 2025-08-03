import os
from concurrent.futures import Future
from pathlib import Path
from typing import TYPE_CHECKING, Callable, List, Tuple, Optional

from typing_extensions import override

from mcdreforged.command.builder.nodes.arguments import QuotableText, Text
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.click_event import RAction
from mcdreforged.minecraft.rtext.style import RColor, RStyle
from mcdreforged.minecraft.rtext.text import RTextList, RText
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdr.commands.plugin_command_pim import PluginCommandPimExtension
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.operation_result import PluginOperationResult, PluginResultType
from mcdreforged.plugin.type.regular_plugin import RegularPlugin

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin
	from mcdreforged.plugin.plugin_manager import PluginManager


class PluginCommand(SubCommand):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)
		self.plugin_manager: 'PluginManager' = self.mcdr_server.plugin_manager
		self.pim_ext = PluginCommandPimExtension(mcdr_plugin)

	@override
	def get_command_node(self) -> Literal:
		def plugin_id_node():
			return Text('plugin_id').suggests(lambda: [plg.get_id() for plg in self.plugin_manager.get_regular_plugins()])

		def unloaded_plugin_node():
			return QuotableText('file_name').suggests(lambda: [os.path.basename(fp) for fp in self.server_interface.get_unloaded_plugin_list()])

		def disabled_plugin_node():
			return QuotableText('file_name').suggests(lambda: [os.path.basename(dp) for dp in self.server_interface.get_disabled_plugin_list()])

		root = (
			self.control_command_root({'plugin', 'plg'}).
			runs(lambda src: self.reply_help_message(src, 'mcdr_command.help_message.plugin')).
			then(Literal('list').runs(self.list_plugin)).
			then(Literal('info').then(plugin_id_node().runs(lambda src, ctx: self.show_plugin_info(src, ctx['plugin_id'])))).
			then(Literal('load').then(unloaded_plugin_node().runs(lambda src, ctx: self.load_plugin(src, ctx['file_name'])))).
			then(Literal('enable').then(disabled_plugin_node().runs(lambda src, ctx: self.enable_plugin(src, ctx['file_name'])))).
			then(Literal('reload').then(plugin_id_node().runs(lambda src, ctx: self.reload_plugin(src, ctx['plugin_id'])))).
			then(Literal('unload').then(plugin_id_node().runs(lambda src, ctx: self.unload_plugin(src, ctx['plugin_id'])))).
			then(Literal('disable').then(plugin_id_node().runs(lambda src, ctx: self.disable_plugin(src, ctx['plugin_id'])))).
			then(Literal({'reloadall', 'ra'}).runs(self.reload_all_plugin))
		)
		for node in self.pim_ext.get_command_child_nodes():
			root.then(node)
		return root

	@override
	def on_load(self):
		self.pim_ext.on_load()

	@override
	def on_mcdr_stop(self):
		self.pim_ext.on_mcdr_stop()

	@override
	def on_event(self, source: Optional[CommandSource], event: SubCommandEvent) -> bool:
		return self.pim_ext.on_event(source, event)

	def list_plugin(self, source: CommandSource):
		not_loaded_plugin_list: List[str] = self.server_interface.get_unloaded_plugin_list()
		disabled_plugin_list: List[str] = self.server_interface.get_disabled_plugin_list()
		current_plugins = list(self.mcdr_server.plugin_manager.get_all_plugins())

		source.reply(self.tr('mcdr_command.list_plugin.info_loaded_plugin', len(current_plugins)))
		for plugin in current_plugins:
			meta = plugin.get_metadata()
			displayed_name = RText(meta.name)
			if not self.can_see_rtext(source):
				displayed_name += RText(' ({})'.format(plugin.get_identifier()), color=RColor.gray)
			texts = RTextList(
				RText('- ', RColor.gray),
				displayed_name.
				c(RAction.run_command, '{} plugin info {}'.format(self.control_command_prefix, meta.id)).
				h(self.tr('mcdr_command.list_plugin.suggest_info', plugin.get_identifier()))
			)
			if self.can_see_rtext(source) and not plugin.is_builtin():
				texts.append(
					' ',
					RText('[↻]', color=RColor.gray)
					.c(RAction.run_command, '{} plugin reload {}'.format(self.control_command_prefix, meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_reload', meta.id)),
					' ',
					RText('[↓]', color=RColor.gray)
					.c(RAction.run_command, '{} plugin unload {}'.format(self.control_command_prefix, meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_unload', meta.id)),
					' ',
					RText('[×]', color=RColor.gray)
					.c(RAction.run_command, '{} plugin disable {}'.format(self.control_command_prefix, meta.id))
					.h(self.tr('mcdr_command.list_plugin.suggest_disable', meta.id))
				)
			source.reply(texts)

		def get_file_name(fp) -> Tuple[str, RText]:
			name = os.path.basename(fp)
			name_text = RText(name)
			if source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL):
				name_text.h(fp)
			return name, name_text

		source.reply(self.tr('mcdr_command.list_plugin.info_disabled_plugin', len(disabled_plugin_list)))
		for file_path in disabled_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.can_see_rtext(source):
				texts.append(
					' ',
					RText('[✔]', color=RColor.gray)
					.c(RAction.run_command, '{} plugin enable {}'.format(self.control_command_prefix, file_name))
					.h(self.tr('mcdr_command.list_plugin.suggest_enable', file_name))
				)
			source.reply(texts)

		source.reply(self.tr('mcdr_command.list_plugin.info_not_loaded_plugin', len(not_loaded_plugin_list)))
		for file_path in not_loaded_plugin_list:
			file_name, file_name_text = get_file_name(file_path)
			texts = RTextList(RText('- ', color=RColor.gray), file_name_text)
			if self.can_see_rtext(source):
				texts.append(
					' ',
					RText('[↑]', color=RColor.gray)
					.c(RAction.run_command, '{} plugin load {}'.format(self.control_command_prefix, file_name))
					.h(self.tr('mcdr_command.list_plugin.suggest_load', file_name))
				)
			source.reply(texts)

	def show_plugin_info(self, source: CommandSource, plugin_id: str):
		plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
		if plugin is None:
			source.reply(self.tr('mcdr_command.invalid_plugin_id', plugin_id))
		else:
			meta = plugin.get_metadata()
			source.reply(RTextList(
				RText(meta.name).set_color(RColor.yellow).set_styles(RStyle.bold).h(plugin),
				' ',
				RText('v{}'.format(meta.version), color=RColor.gray)
			))
			source.reply(self.tr('mcdr_command.plugin_info.id', meta.id))
			if meta.author is not None:
				source.reply(self.tr('mcdr_command.plugin_info.author', ', '.join(meta.author)))
			if meta.link is not None:
				source.reply(self.tr('mcdr_command.plugin_info.link', RText(meta.link, color=RColor.blue, styles=RStyle.underlined).c(RAction.open_url, meta.link)))
			if meta.description is not None:
				source.reply(meta.get_description_rtext())

	def __execute_and_report_plugin_manipulate(
			self, source: CommandSource, operation_name: str, func: Callable[[], 'Future[PluginOperationResult]'],
			plugin_alias: str, result_type_to_check_success: PluginResultType
	):
		ret = self.function_call(source, func, operation_name, reply_success=False, msg_args=(plugin_alias,))
		if ret.no_error:
			def report(fut: 'Future[PluginOperationResult]'):
				if fut.result().get_if_success(result_type_to_check_success):
					source.reply(self.tr('mcdr_command.{}.success'.format(operation_name), plugin_alias))
				else:
					source.reply(self.tr('mcdr_command.{}.fail'.format(operation_name), plugin_alias))

			ret.return_value.add_done_callback(report)
		else:
			source.reply(self.tr('mcdr_command.{}.fail'.format(operation_name), plugin_alias))
		self._print_plugin_operation_result_if_no_error(source, ret)

	def __not_loaded_plugin_file_manipulate(
			self, source: CommandSource, file_name: str, func: Callable[[Path], 'Future[PluginOperationResult]'],
			operation_name: str, possible_plugin_path: List[str]
	):
		possible_plugin_path = [Path(fp) for fp in possible_plugin_path]
		plugin_paths = [fp for fp in possible_plugin_path if str(fp) == str(Path(file_name))]  # try full-match
		if len(plugin_paths) == 0:
			plugin_paths = [fp for fp in possible_plugin_path if fp.name == file_name]  # try name-match
		if len(plugin_paths) == 0:
			source.reply(self.tr('mcdr_command.invalid_plugin_file_name', file_name))
		else:
			self.__execute_and_report_plugin_manipulate(source, operation_name, lambda: func(plugin_paths[0]), file_name, PluginResultType.LOAD)

	def __existed_regular_plugin_manipulate(
			self, source: CommandSource, plugin_id: str, func: Callable[[RegularPlugin], 'Future[PluginOperationResult]'],
			operation_name: str, result_type_to_check_success: PluginResultType
	):
		plugin = self.mcdr_server.plugin_manager.get_regular_plugin_from_id(plugin_id)
		if plugin is None or not plugin.is_regular():
			source.reply(self.tr('mcdr_command.invalid_plugin_id', plugin_id))
		else:
			self.__execute_and_report_plugin_manipulate(source, operation_name, lambda: func(plugin), plugin.get_name(), result_type_to_check_success)

	def disable_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, self.plugin_manager.disable_plugin, 'disable_plugin', PluginResultType.UNLOAD)

	def reload_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, self.plugin_manager.reload_plugin, 'reload_plugin', PluginResultType.RELOAD)

	def unload_plugin(self, source: CommandSource, plugin_id: str):
		self.__existed_regular_plugin_manipulate(source, plugin_id, self.plugin_manager.unload_plugin, 'unload_plugin', PluginResultType.UNLOAD)

	def load_plugin(self, source: CommandSource, file_name: str):
		self.__not_loaded_plugin_file_manipulate(source, file_name, self.plugin_manager.load_plugin, 'load_plugin', self.server_interface.get_unloaded_plugin_list())

	def enable_plugin(self, source: CommandSource, file_name: str):
		self.__not_loaded_plugin_file_manipulate(source, file_name, self.plugin_manager.enable_plugin, 'enable_plugin', self.server_interface.get_disabled_plugin_list())

	def reload_all_plugin(self, source: CommandSource):
		ret = self.function_call(source, self.mcdr_server.plugin_manager.refresh_all_plugins, 'reload_all_plugin', reply_success=False)
		self._print_plugin_operation_result_if_no_error(source, ret)
