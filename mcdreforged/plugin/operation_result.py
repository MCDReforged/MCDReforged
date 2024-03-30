import dataclasses
import os
from enum import Enum
from pathlib import Path
from typing import List, TYPE_CHECKING, NamedTuple, Callable, Union

from mcdreforged.minecraft.rtext.style import RAction
from mcdreforged.minecraft.rtext.text import RTextList, RTextBase, RText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class SingleOperationResult:
	def __init__(self):
		self.success_list: List['AbstractPlugin'] = []
		self.failed_list: List[Union['AbstractPlugin', Path]] = []

	def succeed(self, plugin: 'AbstractPlugin'):
		self.success_list.append(plugin)

	def fail(self, plugin: Union['AbstractPlugin', Path]):
		self.failed_list.append(plugin)

	def record(self, plugin: Union['AbstractPlugin', Path], result: bool):
		if result:
			self.succeed(plugin)
		else:
			self.fail(plugin)

	def __len__(self) -> int:
		return len(self.success_list) + len(self.failed_list)

	def is_success_or_empty(self) -> bool:
		return self.has_success() or len(self) == 0

	def has_success(self) -> bool:
		return len(self.success_list) > 0

	def has_failed(self) -> bool:
		return len(self.failed_list) > 0


class PluginResultType(Enum):
	class _TypeImpl(NamedTuple):
		result_extractor: Callable[['PluginOperationResult'], 'SingleOperationResult']
		check_dependency: bool

	LOAD = _TypeImpl(lambda result: result.load_result, True)
	UNLOAD = _TypeImpl(lambda result: result.unload_result, False)
	RELOAD = _TypeImpl(lambda result: result.reload_result, True)


@dataclasses.dataclass(frozen=True)
class PluginOperationResult:
	load_result: SingleOperationResult
	unload_result: SingleOperationResult
	reload_result: SingleOperationResult
	dependency_check_result: SingleOperationResult

	@classmethod
	def of_empty(cls) -> 'PluginOperationResult':
		empty = SingleOperationResult()
		return PluginOperationResult(empty, empty, empty, empty)

	def get_if_success(self, result_type: PluginResultType) -> bool:
		"""
		Check if there's any plugin inside the given operation result (load result / reload result etc.)
		Then check if the plugin passed the dependency check if param check_loaded is True
		"""
		target_result = result_type.value.result_extractor(self)
		success = target_result.has_success()
		if success and result_type.value.check_dependency:
			plugin = target_result.success_list[0]
			success = plugin in self.dependency_check_result.success_list
		return success

	def to_rtext(self, mcdr_server: 'MCDReforgedServer', *, show_path: bool) -> RTextBase:
		def add_element(msg: RTextList, element):
			msg.append(element)
			msg.append('; ')

		def add_if_not_empty(msg: RTextList, lst: List['AbstractPlugin' or str], key: str):
			if len(lst) > 0:
				text_list = []
				for ele in lst:
					if isinstance(ele, str):
						text_list.append(ele if show_path else os.path.basename(ele))
					else:
						text_list.append(str(ele))
				add_element(msg, RText(mcdr_server.tr(key, len(lst))).h('\n'.join(text_list)))

		message = RTextList()
		add_if_not_empty(message, list(filter(lambda plg: plg in self.dependency_check_result.success_list, self.load_result.success_list)), 'plugin_operation_result.info_loaded_succeeded')
		add_if_not_empty(message, self.unload_result.success_list, 'plugin_operation_result.info_unloaded_succeeded')
		add_if_not_empty(message, self.reload_result.success_list, 'plugin_operation_result.info_reloaded_succeeded')
		add_if_not_empty(message, self.load_result.failed_list, 'plugin_operation_result.info_loaded_failed')
		add_if_not_empty(message, self.unload_result.failed_list, 'plugin_operation_result.info_unloaded_failed')
		add_if_not_empty(message, self.reload_result.failed_list, 'plugin_operation_result.info_reloaded_failed')
		add_if_not_empty(message, self.dependency_check_result.failed_list, 'plugin_operation_result.info_dependency_check_failed')
		if message.is_empty():
			add_element(message, mcdr_server.tr('plugin_operation_result.info_none'))
		message.append(
			RText(mcdr_server.tr('plugin_operation_result.info_plugin_amount', mcdr_server.plugin_manager.get_plugin_amount())).
				h('\n'.join(map(str, mcdr_server.plugin_manager.get_all_plugins()))).
				c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return message
