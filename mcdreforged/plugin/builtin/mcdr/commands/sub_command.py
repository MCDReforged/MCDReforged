import dataclasses
import enum
import traceback
from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import TYPE_CHECKING, Callable, Generic, TypeVar

from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.tools import Requirements
from mcdreforged.command.command_source import CommandSource
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.operation_result import PluginOperationResult
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import class_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin
	from mcdreforged.plugin.si.plugin_server_interface import PluginServerInterface


T = TypeVar('T')


@dataclasses.dataclass(frozen=True)
class FunctionCallResult(Generic[T]):
	return_value: T
	no_error: bool


class SubCommandEvent(enum.Enum):
	confirm = enum.auto()
	abort = enum.auto()


class SubCommand(ABC):
	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		self.mcdr_plugin = mcdr_plugin

	@abstractmethod
	def get_command_node(self) -> Literal:
		raise NotImplementedError()

	def on_load(self):
		pass

	def on_mcdr_stop(self):
		pass

	def on_event(self, source: CommandSource, event: SubCommandEvent) -> bool:
		return False

	# ------------------
	#    Common Utils
	# ------------------

	def tr(self, key: str, *args, **kwargs) -> RTextMCDRTranslation:
		return self.mcdr_plugin.tr(key, *args, **kwargs)

	def log_debug(self, *args, **kwargs):
		kwargs['option'] = DebugOption.COMMAND
		kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1
		logger = class_utils.check_type(self.server_interface.logger, MCDReforgedLogger)
		logger.mdebug(*args, **kwargs)

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
	def owner_command_root(literal) -> Literal:
		return Literal(literal).precondition(Requirements.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL))

	@staticmethod
	def control_command_root(literal) -> Literal:
		return Literal(literal).precondition(Requirements.has_permission(PermissionLevel.MCDR_CONTROL_LEVEL))

	@staticmethod
	def public_command_root(literal) -> Literal:
		return Literal(literal).requires(Requirements.has_permission(PermissionLevel.USER))

	@staticmethod
	def can_see_rtext(source: CommandSource) -> bool:
		return source.is_player

	# ---------------------------------
	#     Refs to MCDReforgedPlugin
	# ---------------------------------

	def reply_help_message(self, source: CommandSource, translation_key: str):
		for line in self.mcdr_plugin.get_help_message(source, translation_key):
			source.reply(line)

	def _print_plugin_operation_result_if_no_error(self, source: CommandSource, ret: FunctionCallResult['Future[PluginOperationResult]']):
		if ret.no_error:
			def reply(fut: 'Future[PluginOperationResult]'):
				source.reply(fut.result().to_rtext(self.mcdr_server, show_path=source.has_permission(PermissionLevel.PHYSICAL_SERVER_CONTROL_LEVEL)))
			ret.return_value.add_done_callback(reply)

	def function_call(
			self, source: CommandSource, func: Callable[[], T], name: str, *,
			reply_success: bool = True, reply_fail: bool = True, msg_args: tuple = ()
	) -> FunctionCallResult[T]:
		try:
			ret = FunctionCallResult(func(), True)
			if reply_success:
				source.reply(self.tr('mcdr_command.{}.success'.format(name), *msg_args))
			return ret
		except Exception:
			if reply_fail:
				source.reply(self.tr('mcdr_command.{}.fail'.format(name), *msg_args))
			self.mcdr_server.logger.error(traceback.format_exc())
			return FunctionCallResult(None, False)
