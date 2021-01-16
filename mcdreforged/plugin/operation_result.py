import os
from typing import List, TYPE_CHECKING

from mcdreforged.minecraft.rtext import RTextList, RText, RAction, RTextBase
from mcdreforged.utils.exception import IllegalCallError

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin import AbstractPlugin
	from mcdreforged.plugin.plugin_manager import PluginManager


class SingleOperationResult:
	def __init__(self):
		self.success_list = []  # type: List['AbstractPlugin']
		self.failed_list = []  # type: List['AbstractPlugin' or str]

	def succeed(self, plugin: 'AbstractPlugin'):
		self.success_list.append(plugin)

	def fail(self, plugin: 'AbstractPlugin' or str):
		self.failed_list.append(plugin)

	def record(self, plugin: 'AbstractPlugin' or str, result: bool):
		if result:
			self.succeed(plugin)
		else:
			self.fail(plugin)

	def has_success(self):
		return len(self.success_list) > 0

	def has_failed(self):
		return len(self.failed_list) > 0


class PluginOperationResult:
	load_result: SingleOperationResult
	unload_result: SingleOperationResult
	reload_result: SingleOperationResult
	dependency_check_result: SingleOperationResult

	def __init__(self, plugin_manager: 'PluginManager'):
		self.__plugin_manager = plugin_manager
		self.__mcdr_server = plugin_manager.mcdr_server
		self.__has_record = False

	def record(self, load_result, unload_result, reload_result, dependencies_resolve_result):
		self.__has_record = True
		self.load_result = load_result
		self.unload_result = unload_result
		self.reload_result = reload_result
		self.dependency_check_result = dependencies_resolve_result

	def to_rtext(self, *, show_path: bool) -> RTextBase:
		if not self.__has_record:
			raise IllegalCallError('No record yet')

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
				add_element(msg, RText(self.__mcdr_server.tr(key, len(lst))).h('\n'.join(text_list)))

		message = RTextList()
		add_if_not_empty(message, list(filter(lambda plg: plg in self.dependency_check_result.success_list, self.load_result.success_list)), 'plugin_operation_result.info_loaded_succeeded')
		add_if_not_empty(message, self.unload_result.success_list, 'plugin_operation_result.info_unloaded_succeeded')
		add_if_not_empty(message, self.reload_result.success_list, 'plugin_operation_result.info_reloaded_succeeded')
		add_if_not_empty(message, self.load_result.failed_list, 'plugin_operation_result.info_loaded_failed')
		add_if_not_empty(message, self.unload_result.failed_list, 'plugin_operation_result.info_unloaded_failed')
		add_if_not_empty(message, self.reload_result.failed_list, 'plugin_operation_result.info_reloaded_failed')
		add_if_not_empty(message, self.dependency_check_result.failed_list, 'plugin_operation_result.info_dependency_check_failed')
		if message.is_empty():
			add_element(message, self.__mcdr_server.tr('plugin_operation_result.info_none'))
		message.append(
			RText(self.__mcdr_server.tr('plugin_operation_result.info_plugin_amount', len(self.__plugin_manager.plugins))).
				h('\n'.join(map(str, self.__plugin_manager.plugins.values()))).
				c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return message
