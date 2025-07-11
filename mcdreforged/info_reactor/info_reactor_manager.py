"""
The place to reacting information from the server
"""
import queue
import time
from typing import TYPE_CHECKING, List, Optional

from mcdreforged.constants import core_constant
from mcdreforged.executor.task_executor_queue import TaskPriority
from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.info_reactor.impl import PlayerReactor, ServerReactor, GeneralReactor
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.info_filter import InfoFilterHolder
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.logger import ServerOutputLogger
from mcdreforged.mcdr_config import MCDReforgedConfig
from mcdreforged.utils import class_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class InfoReactorManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.last_queue_full_warn_time = None
		self.server_output_logger = ServerOutputLogger('Server', mcdr_server.logger)
		self.reactors: List[AbstractInfoReactor] = []
		self.__tr = mcdr_server.create_internal_translator('info_reactor_manager').tr
		self.__info_filter_holders: List[InfoFilterHolder] = []

		mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, config: MCDReforgedConfig, log: bool):
		self.register_reactors(config.custom_info_reactors)

	def set_info_filters(self, info_filter_holders: List[InfoFilterHolder]):
		self.__info_filter_holders = info_filter_holders

	def register_reactors(self, custom_reactor_class_paths: Optional[List[str]]):
		self.reactors.clear()
		self.reactors.extend([
			GeneralReactor(self.mcdr_server),
			ServerReactor(self.mcdr_server),
			PlayerReactor(self.mcdr_server)
		])
		if custom_reactor_class_paths is not None:
			for class_path in custom_reactor_class_paths:
				try:
					reactor_class = class_utils.load_class(class_path)
				except Exception:
					self.mcdr_server.logger.exception('Fail to load info reactor from {!r}'.format(class_path))
				else:
					if issubclass(reactor_class, AbstractInfoReactor):
						self.reactors.append(reactor_class(self.mcdr_server))
						self.mcdr_server.logger.mdebug('Loaded info reactor {} from {}'.format(reactor_class.__name__, class_path), option=DebugOption.REACTOR)
					else:
						self.mcdr_server.logger.error('Wrong reactor class {!r}, expected {} but found {}'.format(class_path, AbstractInfoReactor, reactor_class))

	def process_info(self, info: Info):
		for reactor in self.reactors:
			try:
				reactor.react(info)
			except Exception:
				self.mcdr_server.logger.exception(self.__tr('react.error', type(reactor).__name__))

		# send command input from the console to the server's stdin
		if info.is_from_console and info.should_send_to_server():
			self.mcdr_server.send(info.content)

	def put_info(self, info: Info):
		info.attach_mcdr_server(self.mcdr_server)

		for ifh in self.__info_filter_holders:
			if ifh.filter.filter_server_info(info) is False:
				if self.mcdr_server.logger.should_log_debug(option=DebugOption.HANDLER):
					self.mcdr_server.logger.debug('Server info is discarded by filter {} from {}'.format(ifh.filter, ifh.plugin))
				return

		# echo info from the server to the console
		if info.is_from_server:
			self.server_output_logger.info(info.raw_content, write_to_mcdr_log_file=self.mcdr_server.config.write_server_output_to_log_file)
		try:
			self.mcdr_server.task_executor.submit(lambda: self.process_info(info), raise_if_full=not info.is_user, priority=TaskPriority.INFO)
		except queue.Full:
			current_time = time.monotonic()
			logging_method = self.mcdr_server.logger.debug
			kwargs = {'option': DebugOption.REACTOR}
			if self.last_queue_full_warn_time is None or current_time - self.last_queue_full_warn_time >= core_constant.REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC:
				logging_method = self.mcdr_server.logger.warning
				kwargs = {}
				self.last_queue_full_warn_time = current_time
			logging_method(self.__tr('info_queue.full'), **kwargs)

	def on_server_start(self):
		for reactor in self.reactors:
			reactor.on_server_start()

	def on_server_stop(self):
		for reactor in self.reactors:
			reactor.on_server_stop()
