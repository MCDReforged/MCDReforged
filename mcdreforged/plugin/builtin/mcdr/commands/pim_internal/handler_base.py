from abc import abstractmethod, ABC
from typing import TYPE_CHECKING

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.logger import MCDReforgedLogger
from mcdreforged.minecraft.rtext.click_event import RAction
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.local_meta_registry import LocalMetaRegistry
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.texts import Texts
from mcdreforged.plugin.installer.types import MetaRegistry, MergedMetaRegistry
from mcdreforged.translation.translator import Translator
from mcdreforged.utils import class_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.builtin.mcdr.commands.plugin_command_pim import PluginCommandPimExtension
	from mcdreforged.plugin.plugin_manager import PluginManager


class PimCommandHandlerBase(ABC):
	def __init__(self, pim_ext: 'PluginCommandPimExtension'):
		self.__pim_ext = pim_ext
		self.server_interface = pim_ext.mcdr_plugin.server_interface
		self.logger: MCDReforgedLogger = class_utils.check_type(self.server_interface.logger, MCDReforgedLogger)
		self.mcdr_server: 'MCDReforgedServer' = pim_ext.mcdr_plugin.mcdr_server
		self.plugin_manager: 'PluginManager' = self.mcdr_server.plugin_manager
		self._tr: Translator = pim_ext.pim_tr
		self._raw_tr = pim_ext.tr

	@abstractmethod
	def process(self, source: CommandSource, context: CommandContext):
		raise NotImplementedError()

	def log_debug(self, *args, **kwargs):
		kwargs['option'] = DebugOption.COMMAND
		self.logger.mdebug(*args, **kwargs)

	def get_cata_meta(self, source: CommandSource) -> MetaRegistry:
		return self.__pim_ext.get_cata_meta(source, ignore_ttl=False)

	def get_merged_cata_meta(self, source: CommandSource) -> MetaRegistry:
		return MergedMetaRegistry(self.get_cata_meta(source), LocalMetaRegistry(self.plugin_manager))

	def browse_cmd(self, plugin_id: str) -> RTextBase:
		return (
			Texts.plugin_id(plugin_id).
			h(self._tr('common.browse_cmd', plugin_id)).
			c(RAction.run_command, '{} plugin browse --id {}'.format(self.__pim_ext.control_command_prefix, plugin_id))
		)
