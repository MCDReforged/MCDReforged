import dataclasses
import os
from enum import Enum
from pathlib import Path
from typing import List, TYPE_CHECKING, Callable, Union

from mcdreforged.minecraft.rtext.click_event import RAction
from mcdreforged.minecraft.rtext.text import RTextList, RTextBase

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


@dataclasses.dataclass(frozen=True)
class _PluginResultTypeImpl:
	result_extractor: Callable[['PluginOperationResult'], 'SingleOperationResult']
	check_dependency: bool

	@staticmethod
	def load_result_getter(result: 'PluginOperationResult') -> 'SingleOperationResult':
		return result.load_result

	@staticmethod
	def unload_result_getter(result: 'PluginOperationResult') -> 'SingleOperationResult':
		return result.unload_result

	@staticmethod
	def reload_result_getter(result: 'PluginOperationResult') -> 'SingleOperationResult':
		return result.reload_result


class PluginResultType(Enum):
	LOAD = _PluginResultTypeImpl(_PluginResultTypeImpl.load_result_getter, True)
	UNLOAD = _PluginResultTypeImpl(_PluginResultTypeImpl.unload_result_getter, False)
	RELOAD = _PluginResultTypeImpl(_PluginResultTypeImpl.reload_result_getter, True)


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

		tr = mcdr_server.create_internal_translator('plugin_operation_result')

		def add_if_not_empty(msg: RTextList, lst: List['AbstractPlugin' or str], key: str):
			if len(lst) > 0:
				text_list = []
				for ele in lst:
					if isinstance(ele, str):
						text_list.append(ele if show_path else os.path.basename(ele))
					else:
						text_list.append(str(ele))
				add_element(msg, tr(key, len(lst)).h('\n'.join(text_list)))

		message = RTextList()
		add_if_not_empty(message, [plg for plg in self.load_result.success_list if plg in self.dependency_check_result.success_list], 'info_loaded_succeeded')
		add_if_not_empty(message, self.unload_result.success_list, 'info_unloaded_succeeded')
		add_if_not_empty(message, self.reload_result.success_list, 'info_reloaded_succeeded')
		add_if_not_empty(message, self.load_result.failed_list, 'info_loaded_failed')
		add_if_not_empty(message, self.unload_result.failed_list, 'info_unloaded_failed')
		add_if_not_empty(message, self.reload_result.failed_list, 'info_reloaded_failed')
		add_if_not_empty(message, self.dependency_check_result.failed_list, 'info_dependency_check_failed')
		if message.is_empty():
			add_element(message, tr('info_none'))
		message.append(
			tr('info_plugin_count', mcdr_server.plugin_manager.get_plugin_amount()).
			h('\n'.join(map(str, mcdr_server.plugin_manager.get_all_plugins()))).
			c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return message
