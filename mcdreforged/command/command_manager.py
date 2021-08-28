"""
Handling MCDR commands
"""
import collections
from enum import Enum, auto
from typing import TYPE_CHECKING, Dict, List

import mcdreforged.command.builder.command_builder_util as utils
from mcdreforged.command.builder.exception import CommandError, RequirementNotMet
from mcdreforged.command.builder.nodes.basic import CommandSuggestion, CommandSuggestions
from mcdreforged.command.command_source import InfoCommandSource, CommandSource
from mcdreforged.plugin.plugin_registry import PluginCommandNode
from mcdreforged.utils import string_util
from mcdreforged.utils.logger import DebugOption

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
		self.tr = self.mcdr_server.tr
		self.root_nodes = collections.defaultdict(list)  # type: Dict[str, List[PluginCommandNode]]

		self.__preserve_command_error_display_flag = False

	def clear_command(self):
		self.root_nodes.clear()

	def register_command(self, plugin_node: PluginCommandNode):
		for literal in plugin_node.node.literals:
			self.root_nodes[literal].append(plugin_node)

	def _traverse(self, command: str, source: CommandSource, purpose: TraversePurpose) -> None or List[CommandSuggestion]:
		def __translate_command_error_header(translation_key_: str, error_: CommandError) -> str:
			if isinstance(error_, RequirementNotMet):
				if error_.has_custom_reason():
					return error_.get_reason()
				args = ()
			else:
				args = error_.get_error_data()
			return self.mcdr_server.tr(translation_key_, *args, allow_failure=False, language=source.get_preference().language)

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
			node = plugin_root_node.node
			try:
				with self.mcdr_server.plugin_manager.with_plugin_context(plugin):
					if purpose == TraversePurpose.EXECUTE:
						node.execute(source, command)
					elif purpose == TraversePurpose.SUGGEST:
						suggestions.extend(node.generate_suggestions(source, command))

			except CommandError as error:
				if not error.is_handled():
					translation_key = 'command_exception.{}'.format(string_util.hump_to_underline(type(error).__name__))
					try:
						error.set_message(__translate_command_error_header(translation_key, error))
					except KeyError:
						self.logger.debug('Fail to translated command error with key {}'.format(translation_key), option=DebugOption.COMMAND)
					source.reply(error.to_rtext())
			except:
				self.logger.exception('Error when executing command "{}" with command source "{}" on {} registered by {}'.format(command, source, node, plugin))

		if purpose == TraversePurpose.SUGGEST:
			return suggestions

	def execute_command(self, command: str, source: CommandSource):
		self._traverse(command, source, TraversePurpose.EXECUTE)

	def suggest_command(self, command: str, source: CommandSource) -> CommandSuggestions:
		return self._traverse(command, source, TraversePurpose.SUGGEST)
