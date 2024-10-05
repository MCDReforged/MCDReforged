"""
Handling MCDR commands
"""
import collections
import contextlib
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List

import mcdreforged.command.builder.command_builder_utils as utils
from mcdreforged.command.builder.exception import CommandError, RequirementNotMet
from mcdreforged.command.builder.nodes.basic import CommandSuggestion, CommandSuggestions, CallbackError, EntryNode
from mcdreforged.command.command_source import InfoCommandSource, CommandSource
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.plugin.plugin_registry import PluginCommandHolder
from mcdreforged.utils import string_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class TraversePurpose(Enum):
	EXECUTE = auto()
	SUGGEST = auto()


# deal with !!MCDR and !!help command
class CommandManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = self.mcdr_server.logger
		self.root_nodes: Dict[str, List[PluginCommandHolder]] = collections.defaultdict(list)

		self.__preserve_command_error_display_flag = False

	@contextlib.contextmanager
	def start_command_register(self):
		self.root_nodes.clear()
		yield self.__register_one_command
		for literal, pch_list in self.root_nodes.items():
			if sum([not pch.allow_duplicates for pch in pch_list]) >= 2:
				self.logger.warning('Found duplicated command root literal {!r}: {}'.format(literal, pch_list))

	def __register_one_command(self, pch: PluginCommandHolder):
		for literal in pch.node.literals:
			self.root_nodes[literal].append(pch)

	def _traverse(self, command: str, source: CommandSource, purpose: TraversePurpose) -> None or List[CommandSuggestion]:
		def __translate_command_error_header(translation_key_: str, error_: CommandError) -> str:
			if isinstance(error_, RequirementNotMet):
				if error_.has_custom_reason():
					return error_.get_reason()
				args = ()
			else:
				args = error_.get_error_data()
			return self.mcdr_server.translate(translation_key_, *args, _mcdr_tr_allow_failure=False, _mcdr_tr_language=source.get_preference().language)

		first_literal_element = utils.get_element(command)
		plugin_root_nodes = self.root_nodes.get(first_literal_element, [])
		suggestions = CommandSuggestions()

		if purpose == TraversePurpose.EXECUTE and isinstance(source, InfoCommandSource):
			if len(plugin_root_nodes) > 0 and source.is_console:
				# If this is a command, don't send it towards the server if it's from console input
				source.get_info().cancel_send_to_server()

		if purpose == TraversePurpose.SUGGEST and len(plugin_root_nodes) == 0:
			return CommandSuggestions([CommandSuggestion('', literal) for literal in self.root_nodes.keys()])

		for plugin_root_node in plugin_root_nodes:
			plugin = plugin_root_node.plugin
			node: EntryNode = plugin_root_node.node
			try:
				with self.mcdr_server.plugin_manager.with_plugin_context(plugin):
					if purpose == TraversePurpose.EXECUTE:
						# noinspection PyProtectedMember
						node._entry_execute(source, command)
					elif purpose == TraversePurpose.SUGGEST:
						# noinspection PyProtectedMember
						suggestions.extend(node._entry_generate_suggestions(source, command))

			except CommandError as error:
				if not error.is_handled():
					translation_key = 'mcdreforged.command_exception.{}'.format(string_utils.hump_to_underline(type(error).__name__))
					try:
						error.set_message(__translate_command_error_header(translation_key, error))
					except KeyError:
						self.logger.mdebug('Fail to translated command error with key {}'.format(translation_key), option=DebugOption.COMMAND)
					source.reply(error.to_rtext())
			except Exception as error:
				data = {
					'source': source,
					'node': node,
					'plugin': plugin
				}
				if isinstance(error, CallbackError):
					data['for'] = error.action
					data['path'] = '[{}]'.format(', '.join(map(str, error.context.node_path)))
					exc_info = error.exc_info
				else:
					exc_info = True
				self.logger.error('Error when executing command {}, {}'.format(
					repr(command),
					', '.join([f'{key}={value!r}' for key, value in data.items()])
				), exc_info=exc_info)

		if purpose == TraversePurpose.SUGGEST:
			return suggestions

	def execute_command(self, command: str, source: CommandSource):
		self._traverse(command, source, TraversePurpose.EXECUTE)

	def suggest_command(self, command: str, source: CommandSource) -> CommandSuggestions:
		return self._traverse(command, source, TraversePurpose.SUGGEST)
