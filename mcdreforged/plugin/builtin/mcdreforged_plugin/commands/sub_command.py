import traceback
from abc import ABC
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.operation_result import PluginOperationResult
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils.future import Future

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin
	from mcdreforged.plugin.server_interface import PluginServerInterface


T = TypeVar('T')


# can't do Generic + NamedTuple
class FunctionCallResult(Generic[T]):
	def __init__(self, return_value: T, no_error: bool):
		self.return_value = return_value
		self.no_error = no_error


class SubCommand(ABC):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		self.mcdr_plugin = mcdr_plugin

	def get_command_node(self) -> Literal:
		raise NotImplementedError()

	# ------------------
	#    Common Utils
	# ------------------

	def tr(self, key: str, *args, **kwargs) -> RTextMCDRTranslation:
		return self.mcdr_plugin.tr(key, *args, **kwargs)

	@property
	def mcdr_server(self) -> 'MCDReforgedServer':
		return self.mcdr_plugin.mcdr_server

	@property
	def server_interface(self) -> 'PluginServerInterface':
		return self.mcdr_plugin.server_interface

	@property
	def control_command_prefix(self) -> str:
		return self.mcdr_plugin.control_command_prefix

	@property
	def help_command_prefix(self) -> str:
		return self.mcdr_plugin.help_command_prefix

	@staticmethod
	def control_command_root(literal) -> Literal:
		return Literal(literal).requires(lambda src: src.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL))

	@staticmethod
	def public_command_root(literal) -> Literal:
		return Literal(literal).requires(lambda src: src.has_permission(PermissionLevel.USER))

	@staticmethod
	def can_see_rtext(source: CommandSource) -> bool:
		return source.is_player

	# ---------------------------------
	#     Refs to MCDReforgedPlugin
	# ---------------------------------

	def get_help_message(self, source: CommandSource, translation_key: str):
		return self.mcdr_plugin.get_help_message(source, translation_key)

	def _print_plugin_operation_result_if_no_error(self, source: CommandSource, ret: FunctionCallResult[Future[PluginOperationResult]]):
		if ret.no_error:
			def reply(result: PluginOperationResult):
				source.reply(result.to_rtext(self.mcdr_server, show_path=source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL)))
			ret.return_value.add_done_callback(reply)

	def function_call(self, source: CommandSource, func: Callable[[], T], name: str, log_success=True, log_fail=True, msg_args=()) -> FunctionCallResult[T]:
		try:
			ret = FunctionCallResult(func(), True)
			if log_success:
				source.reply(self.tr('mcdr_command.{}.success'.format(name), *msg_args))
			return ret
		except:
			if log_fail:
				source.reply(self.tr('mcdr_command.{}.fail'.format(name), *msg_args))
			self.mcdr_server.logger.error(traceback.format_exc())
			return FunctionCallResult(None, False)
