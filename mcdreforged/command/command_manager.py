"""
Handling MCDR commands
"""
import sys
from typing import TYPE_CHECKING, Dict, List

import mcdreforged.command.builder.command_builder_util as utils
from mcdreforged.command.builder.command_node import Literal
from mcdreforged.command.builder.exception import CommandError
from mcdreforged.command.command_source import CommandSource, CommandSourceType
from mcdreforged.utils import string_util
from mcdreforged.utils.logger import DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


# deal with !!MCDR and !!help command
class CommandManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = self.mcdr_server.logger
		self.tr = self.mcdr_server.tr
		self.root_nodes = {}  # type: Dict[str, List[Literal]]

		self.__preserve_command_error_display_flag = False

	def clear_command(self):
		self.root_nodes.clear()

	def register_command(self, root_node: Literal):
		if not isinstance(root_node, Literal):
			raise TypeError('Only Literal node is accpeted to be a root node')
		for literal in root_node.literals:
			nodes = self.root_nodes.get(literal, [])
			nodes.append(root_node)
			self.root_nodes[literal] = nodes

	def execute_command(self, source: CommandSource, command: str):
		first_literal_element = utils.get_element(command)
		root_nodes = self.root_nodes.get(first_literal_element, [])
		if len(root_nodes) > 0 and source.source_type == CommandSourceType.CONSOLE:
			# If this is a command, don't send it towards the server if it's from console input
			source.get_info().cancel_send_to_server()

		command_errors = []
		general_exc_info = []
		for node in root_nodes:
			try:
				node.execute(source, command)
			except CommandError as e:
				command_errors.append(e)
			except:
				general_exc_info.append(sys.exc_info())
		for exc_info in general_exc_info:
			self.logger.error('Error when executing command "{}" with command source "{}"'.format(command, source), exc_info=exc_info)
		for error in command_errors:
			if not error.is_handled():
				translation_key = 'command_exception.{}'.format(string_util.hump_to_underline(type(error).__name__))
				try:
					error.set_translated_message(translation_key, lambda key, args: self.mcdr_server.tr(key, *args, allow_failure=False))
				except KeyError:
					self.logger.debug('Fail to translated command error with key {}'.format(translation_key), option=DebugOption.COMMAND)
				source.reply(error.to_mc_color_text())
