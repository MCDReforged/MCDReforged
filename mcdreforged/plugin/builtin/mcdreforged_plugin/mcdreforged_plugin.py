import re

from mcdreforged.command.builder.exception import RequirementNotMet, UnknownArgument, CommandError
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RText, RAction, RTextList, RColor
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.check_update_command import CheckUpdateCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.help_command import HelpCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.permission_command import PermissionCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.plugin_command import PluginCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.preference_command import PreferenceCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.reload_command import ReloadCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.status_command import StatusCommand
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.permanent_plugin import PermanentPlugin
from mcdreforged.translation.translation_text import RTextMCDRTranslation

METADATA = {
	'id': core_constant.NAME.lower(),
	'version': core_constant.VERSION,
	'name': core_constant.NAME,
	'description': 'The core of {}'.format(core_constant.NAME),
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/Fallen-Breath/MCDReforged'
}


class MCDReforgedPlugin(PermanentPlugin):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager)
		self._set_metadata(Metadata(METADATA, plugin=self))
		self.command_help = HelpCommand(self)
		self.command_status = StatusCommand(self)
		self.command_reload = ReloadCommand(self)
		self.command_permission = PermissionCommand(self)
		self.command_plugin = PluginCommand(self)
		self.command_check_update = CheckUpdateCommand(self)
		self.command_preference = PreferenceCommand(self)

	def tr(self, key: str, *args, **kwargs) -> RTextMCDRTranslation:
		return self.server_interface.rtr(key, *args, **kwargs)

	def load(self):
		self.plugin_registry.clear()
		self.__register_commands()
		self.server_interface.register_help_message(self.control_command_prefix, self.tr('mcdr_command.help_message.mcdr_command'))
		self.server_interface.register_help_message(self.help_command_prefix, self.tr('mcdr_command.help_message.help_command'))

	def __repr__(self):
		# avoid using self.metadata here since it might not be initialized
		return 'MCDReforgedPlugin[version={}]'.format(METADATA['version'])

	@property
	def control_command_prefix(self):
		return '!!MCDR'

	@property
	def help_command_prefix(self):
		return '!!help'

	def __register_commands(self):
		self.register_command(
			Literal(self.control_command_prefix).
			requires(lambda src: src.has_permission(PermissionLevel.USER)).
			runs(self.process_mcdr_command).
			on_error(RequirementNotMet, self.on_mcdr_command_permission_denied, handled=True).
			on_child_error(RequirementNotMet, self.on_mcdr_command_permission_denied, handled=True).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument, handled=True).
			then(self.command_status.get_command_node()).
			then(self.command_reload.get_command_node()).
			then(self.command_permission.get_command_node()).
			then(self.command_plugin.get_command_node()).
			then(self.command_check_update.get_command_node()).
			then(self.command_preference.get_command_node())
		)
		self.register_command(self.command_help.get_command_node())

	# --------------------
	#    Command Stuffs
	# --------------------

	def get_help_message(self, source: CommandSource, translation_key: str):
		lst = RTextList()
		with source.preferred_language_context():
			for line in self.tr(translation_key).to_plain_text().splitlines(keepends=True):
				prefix = re.search(r'(?<=§7)' + self.control_command_prefix + r'[\w ]*(?=§)', line)
				if prefix is not None:
					lst.append(RText(line).c(RAction.suggest_command, prefix.group()))
				else:
					lst.append(line)
		return lst

	def on_mcdr_command_permission_denied(self, source: CommandSource, error: CommandError):
		if not error.is_handled():
			source.reply(RText(self.mcdr_server.tr('mcdr_command.permission_denied'), color=RColor.red))

	def on_mcdr_command_unknown_argument(self, source: CommandSource, error: CommandError):
		if source.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL):
			command = error.get_parsed_command().rstrip(' ')
			source.reply(
				RText(self.tr('mcdr_command.command_not_found', command)).
				h(self.tr('mcdr_command.command_not_found_suggest', command)).
				c(RAction.run_command, command)
			)
		else:
			self.on_mcdr_command_permission_denied(source, error)

	def process_mcdr_command(self, source: CommandSource):
		if source.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL):
			source.reply(self.get_help_message(source, 'mcdr_command.help_message'))
		else:
			self.command_status.print_mcdr_status(source)
