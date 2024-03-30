import functools
import re
from typing import List, TYPE_CHECKING

from typing_extensions import override

from mcdreforged.command.builder.exception import RequirementNotMet, UnknownArgument, CommandError
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext.style import RColor, RAction
from mcdreforged.minecraft.rtext.text import RText, RTextBase
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.abort_subcommand import AbortSubCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.check_update_command import CheckUpdateCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.confirm_subcommand import ConfirmSubCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.debug_command import DebugCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.help_command import HelpCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.permission_command import PermissionCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.plugin_command import PluginCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.preference_command import PreferenceCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.reload_command import ReloadCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.server_command import ServerCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.status_command import StatusCommand
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.plugin_event import MCDRPluginEvents
from mcdreforged.plugin.type.permanent_plugin import PermanentPlugin
from mcdreforged.translation.translation_text import RTextMCDRTranslation

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


METADATA = {
	'id': core_constant.PACKAGE_NAME,
	'version': core_constant.VERSION,
	'name': core_constant.NAME,
	'description': 'The core of {}'.format(core_constant.NAME),
	'author': [
		'Fallen_Breath'
	],
	'link': core_constant.GITHUB_URL
}


class MCDReforgedPlugin(PermanentPlugin):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__(plugin_manager)
		self._set_metadata(Metadata(METADATA, plugin=self))
		self.command_help = HelpCommand(self)
		self.command_status = StatusCommand(self)
		self.main_sub_commands: List[SubCommand] = [
			AbortSubCommand(self, functools.partial(self.dispatch_sub_command_event, event=SubCommandEvent.abort)),
			CheckUpdateCommand(self),
			ConfirmSubCommand(self, functools.partial(self.dispatch_sub_command_event, event=SubCommandEvent.confirm)),
			DebugCommand(self),
			PermissionCommand(self),
			PluginCommand(self),
			PreferenceCommand(self),
			ReloadCommand(self),
			ServerCommand(self),
			self.command_status,
		]

	def tr(self, key: str, *args, **kwargs) -> RTextMCDRTranslation:
		return self.server_interface.rtr(key, *args, **kwargs)

	@override
	def load(self):
		self.plugin_registry.clear()
		self.__register_commands()
		self.server_interface.register_help_message(self.control_command_prefix, self.tr('mcdr_command.help_message.mcdr_command'))
		self.server_interface.register_help_message(self.help_command_prefix, self.tr('mcdr_command.help_message.help_command'))

		def on_load():
			for sub_command in self.main_sub_commands:
				sub_command.on_load()

		def on_mcdr_stop(_):
			for sub_command in self.main_sub_commands:
				sub_command.on_mcdr_stop()

		self.server_interface.register_event_listener(MCDRPluginEvents.MCDR_STOP, on_mcdr_stop)
		on_load()

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
		main_root = (
			Literal(self.control_command_prefix).
			requires(lambda src: src.has_permission(PermissionLevel.USER)).
			runs(self.process_mcdr_command).
			on_error(RequirementNotMet, self.on_mcdr_command_permission_denied, handled=True).
			on_error(UnknownArgument, self.on_mcdr_command_unknown_argument).
			on_child_error(RequirementNotMet, self.on_mcdr_command_permission_denied, handled=True).
			on_child_error(UnknownArgument, self.on_mcdr_command_unknown_argument)
		)
		for sub_command in self.main_sub_commands:
			main_root.then(sub_command.get_command_node())
		self.register_command(main_root)
		self.register_command(self.command_help.get_command_node())

	# --------------------
	#    Command Stuffs
	# --------------------

	def get_help_message(self, source: CommandSource, translation_key: str) -> List[RTextBase]:
		lst = []
		with source.preferred_language_context():
			for line in self.tr(translation_key).to_plain_text().splitlines(keepends=False):
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
			for line in self.get_help_message(source, 'mcdr_command.help_message'):
				source.reply(line)
		else:
			self.command_status.print_mcdr_status(source)

	def dispatch_sub_command_event(self, source: CommandSource, event: SubCommandEvent):
		handled = False
		for sub_command in self.main_sub_commands:
			handled |= sub_command.on_event(source, event)

		if event == SubCommandEvent.confirm:
			if not handled:
				source.reply('Nothing to confirm')
		elif event == SubCommandEvent.abort:
			if not handled:
				source.reply('Nothing to abort')
