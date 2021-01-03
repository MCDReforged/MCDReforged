from typing import List

from mcdr.exception import IllegalCall
from mcdr.plugin.plugin import Plugin
from mcdr.rtext import RTextList, RText, RAction, RTextBase


class SingleOperationResult:
	def __init__(self):
		self.success_list = []  # type: List[Plugin]
		self.failed_list = []  # type: List[Plugin or str]

	def succeed(self, plugin: Plugin):
		self.success_list.append(plugin)

	def fail(self, plugin: Plugin or str):
		self.failed_list.append(plugin)

	def record(self, plugin: Plugin or str, result: bool):
		if result:
			self.succeed(plugin)
		else:
			self.fail(plugin)


class PluginOperationResult:
	load_result: SingleOperationResult
	unload_result: SingleOperationResult
	reload_result: SingleOperationResult
	dependency_check_result: SingleOperationResult

	def __init__(self, plugin_manager):
		self.plugin_manager = plugin_manager
		self.mcdr_server = plugin_manager.mcdr_server
		self.has_record = False

	def record(self, load_result, unload_result, reload_result, dependencies_resolve_result):
		self.has_record = True
		self.load_result = load_result
		self.unload_result = unload_result
		self.reload_result = reload_result
		self.dependency_check_result = dependencies_resolve_result

	def to_rtext(self) -> RTextBase:
		if not self.has_record:
			raise IllegalCall('No record yet')

		def add_element(msg: RTextList, element):
			msg.append(element)
			msg.append('; ')

		def add_if_not_empty(msg: RTextList, lst: List[Plugin or str], key: str):
			if len(lst) > 0:
				add_element(msg, RText(self.mcdr_server.tr(key, len(lst))).h('\n'.join(map(str, lst))))

		message = RTextList()
		add_if_not_empty(message, self.load_result.success_list, 'plugin_operation_result.info_loaded_succeeded')
		add_if_not_empty(message, self.unload_result.success_list, 'plugin_operation_result.info_unloaded_succeeded')
		add_if_not_empty(message, self.reload_result.success_list, 'plugin_operation_result.info_reloaded_succeeded')
		add_if_not_empty(message, self.load_result.failed_list, 'plugin_operation_result.info_loaded_failed')
		add_if_not_empty(message, self.unload_result.failed_list, 'plugin_operation_result.info_unloaded_failed')
		add_if_not_empty(message, self.reload_result.failed_list, 'plugin_operation_result.info_reloaded_failed')
		add_if_not_empty(message, self.dependency_check_result.failed_list, 'plugin_operation_result.info_dependency_check_failed')
		if message.empty():
			add_element(message, self.mcdr_server.tr('plugin_operation_result.info_none'))
		message.append(
			RText(self.mcdr_server.tr('plugin_operation_result.info_plugin_amount', len(self.plugin_manager.plugins))).
				h('\n'.join(map(str, self.plugin_manager.plugins.values()))).
				c(RAction.suggest_command, '!!MCDR plugin list')
		)
		return message
