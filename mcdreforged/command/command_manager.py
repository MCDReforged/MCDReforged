"""
Handling MCDR commands
"""
import collections
import contextlib
from typing import TYPE_CHECKING, Dict, List, Tuple, Callable, Coroutine, Iterable, ContextManager, TypeVar

from typing_extensions import override

import mcdreforged.command.builder.command_builder_utils as utils
from mcdreforged.command.builder.callback import CallbackError, CallbackInvoker
from mcdreforged.command.builder.common import CommandExecution
from mcdreforged.command.builder.exception import CommandError, RequirementNotMet
from mcdreforged.command.builder.nodes.basic import CommandSuggestion, CommandSuggestions, EntryNode
from mcdreforged.command.command_source import InfoCommandSource, CommandSource
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.plugin.plugin_registry import PluginCommandHolder
from mcdreforged.utils import string_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin

_T = TypeVar('_T')


class CommandExecutionInvoker(CallbackInvoker):
	def __init__(self, mcdr_server: 'MCDReforgedServer', pch: PluginCommandHolder, context_manager_func: Callable[[], ContextManager]):
		self.__mcdr_server = mcdr_server
		self.__pch = pch
		self.__context_manager_func = context_manager_func

	@override
	def invoke_sync(self, func: Callable[..., _T], args: Iterable) -> None:
		def sync_command_execution_wrapper():
			with self.__context_manager_func():
				func(*args)

		# TODO: submit as a task?
		# self.__mcdr_server.task_executor.submit(sync_command_execution_wrapper, plugin=self.__pch.plugin)
		sync_command_execution_wrapper()  # FIXME: SyncTaskExecutor.get_running_plugin will not return the command's plugin

	@override
	def invoke_async(self, func: Callable[..., Coroutine], args: Iterable) -> None:
		async def async_command_execution_wrapper():
			with self.__context_manager_func():
				await func(*args)

		self.__mcdr_server.async_task_executor.submit(async_command_execution_wrapper(), plugin=self.__pch.plugin)


class CommandManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = self.mcdr_server.logger
		self.root_nodes: Dict[str, List[PluginCommandHolder]] = {}

		self.__preserve_command_error_display_flag = False

	@contextlib.contextmanager
	def start_command_register(self):
		def register_one_command(pch: PluginCommandHolder):
			for literal_ in pch.node.literals:
				new_root_nodes[literal_].append(pch)

		new_root_nodes: Dict[str, List[PluginCommandHolder]] = collections.defaultdict(list)
		yield register_one_command
		for literal, pch_list in new_root_nodes.items():
			if sum([not pch.allow_duplicates for pch in pch_list]) >= 2:
				self.logger.warning('Found duplicated command root literal {!r}: {}'.format(literal, pch_list))
		self.root_nodes = dict(new_root_nodes)  # no more defaultdict

	def __translate_command_error_header(self, source: CommandSource, translation_key_: str, error_: CommandError) -> str:
		if isinstance(error_, RequirementNotMet):
			if error_.has_custom_reason():
				return error_.get_reason()
			args = ()
		else:
			args = error_.get_error_data()
		return self.mcdr_server.translate(translation_key_, *args, _mcdr_tr_allow_failure=False, _mcdr_tr_language=source.get_preference().language)

	@contextlib.contextmanager
	def __handle_command_context_and_error(self, source: CommandSource, command: str, plugin: 'AbstractPlugin', node: EntryNode):
		try:
			with self.mcdr_server.plugin_manager.with_plugin_context(plugin):
				yield
		except CommandError as error:
			if not error.is_handled():
				translation_key = 'mcdreforged.command_exception.{}'.format(string_utils.hump_to_underline(type(error).__name__))
				try:
					error.set_message(self.__translate_command_error_header(source, translation_key, error))
				except KeyError:
					self.logger.mdebug('Fail to translated command error with key {}'.format(translation_key), option=DebugOption.COMMAND)
				source.reply(error.to_rtext())
		except Exception as error:
			data = {
				'source': source,
				'node': node,
				'plugin': plugin,
			}
			if isinstance(error, CallbackError):
				data['for'] = error.action
				data['path'] = error.context.node_path
				exc_info = error.exc_info
			else:
				exc_info = True
			self.logger.error('Error when executing command {}, {}'.format(
				repr(command),
				', '.join(f'{key}={value!r}' for key, value in data.items())
			), exc_info=exc_info)

	def __create_command_context_func(self, source: CommandSource, command: str, execution: CommandExecution, pch: PluginCommandHolder) -> Callable[[], ContextManager]:
		@contextlib.contextmanager
		def contextmanager_func():
			with self.__handle_command_context_and_error(source, command, pch.plugin, pch.node):
				with execution.scheduled_callback.wrap_callback_error():
					yield

		# stupid pycharm cannot infer this
		# noinspection PyTypeChecker
		return contextmanager_func

	def execute_command(self, command: str, source: CommandSource):
		plugin_root_nodes = self.root_nodes.get(utils.get_element(command), [])

		if isinstance(source, InfoCommandSource):
			if len(plugin_root_nodes) > 0 and source.is_console:
				# If this is a command, don't send it towards the server if it's from console input
				source.get_info().cancel_send_to_server()

		executions: List[Tuple[CommandExecution, PluginCommandHolder]] = []
		for pch in plugin_root_nodes:
			with self.__handle_command_context_and_error(source, command, pch.plugin, pch.node):
				# noinspection PyProtectedMember
				for execution in pch.node._entry_execute(source, command):
					executions.append((execution, pch))

		for execution, pch in executions:
			invoker = CommandExecutionInvoker(self.mcdr_server, pch, self.__create_command_context_func(source, command, execution, pch))
			execution.scheduled_callback.invoke(invoker)

	def suggest_command(self, command: str, source: CommandSource) -> CommandSuggestions:
		plugin_root_nodes = self.root_nodes.get(utils.get_element(command), [])
		if len(plugin_root_nodes) == 0:
			return CommandSuggestions([CommandSuggestion('', literal) for literal in self.root_nodes.keys()])

		suggestions = CommandSuggestions()
		for pch in plugin_root_nodes:
			with self.__handle_command_context_and_error(source, command, pch.plugin, pch.node):
				# noinspection PyProtectedMember
				suggestions.extend(pch.node._entry_generate_suggestions(source, command))

		return suggestions
