"""
The place to reacting information from the server
"""
import queue
import time
from typing import TYPE_CHECKING, List

from mcdreforged import constant
from mcdreforged.info import Info, InfoSource
from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import ServerLogger, DebugOption

if TYPE_CHECKING:
	from mcdreforged import MCDReforgedServer


class InfoReactorManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.last_queue_full_warn_time = None
		self.server_logger = ServerLogger('Server')
		self.reactors = []  # type: List[AbstractInfoReactor]

	def load_reactors(self, reactor_class_paths: List[str]):
		self.reactors.clear()
		for class_path in reactor_class_paths:
			try:
				reactor_class = misc_util.load_class(class_path)
			except:
				self.mcdr_server.logger.exception('Fail to load info reactor from "{}"'.format(class_path))
			else:
				if issubclass(reactor_class, AbstractInfoReactor):
					reactor = reactor_class(self.mcdr_server)
					self.reactors.append(reactor)
					self.mcdr_server.logger.debug('Loaded info reactor {} from {}'.format(reactor_class.__name__, class_path), option=DebugOption.REACTOR)
				else:
					self.mcdr_server.logger.exception('Wrong reactor class "{}", expected {} but found {}'.format(class_path, AbstractInfoReactor, reactor_class))

	def process_info(self, info: Info):
		for reactor in self.reactors:
			try:
				reactor.react(info)
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('info_reactor_manager.react.error', type(reactor).__name__))
		self.__post_process_info(info)

	def __post_process_info(self, info: Info):
		if info.source == InfoSource.SERVER and info.should_echo():
			self.server_logger.info(info.raw_content)

		if info.source == InfoSource.CONSOLE and info.should_send_to_server():
			self.mcdr_server.send(info.content)  # send input command to server's stdin

	def put_info(self, info):
		info.attach_mcdr_server(self.mcdr_server)
		try:
			self.mcdr_server.task_executor.add_info_task(lambda: self.process_info(info), info.is_user)
		except queue.Full:
			current_time = time.time()
			logging_method = self.mcdr_server.logger.debug
			kwargs = {'option': DebugOption.REACTOR}
			if self.last_queue_full_warn_time is None or current_time - self.last_queue_full_warn_time >= constant.REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC:
				logging_method = self.mcdr_server.logger.warning
				kwargs = {}
				self.last_queue_full_warn_time = current_time
			logging_method(self.mcdr_server.tr('info_reactor_manager.info_queue.full'), **kwargs)
