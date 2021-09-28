"""
The place to reacting information from the server
"""
import queue
import time
from typing import TYPE_CHECKING, List, Optional

from mcdreforged.constants import core_constant
from mcdreforged.info_reactor.abstract_info_reactor import AbstractInfoReactor
from mcdreforged.info_reactor.impl import PlayerReactor, ServerReactor, GeneralReactor
from mcdreforged.info_reactor.info import Info
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import ServerLogger, DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class InfoReactorManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.last_queue_full_warn_time = None
		self.server_logger = ServerLogger('Server')
		self.reactors = []  # type: List[AbstractInfoReactor]

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
					reactor_class = misc_util.load_class(class_path)
				except:
					self.mcdr_server.logger.exception('Fail to load info reactor from "{}"'.format(class_path))
				else:
					if issubclass(reactor_class, AbstractInfoReactor):
						self.reactors.append(reactor_class(self.mcdr_server))
						self.mcdr_server.logger.debug('Loaded info reactor {} from {}'.format(reactor_class.__name__, class_path), option=DebugOption.REACTOR)
					else:
						self.mcdr_server.logger.error('Wrong reactor class "{}", expected {} but found {}'.format(class_path, AbstractInfoReactor, reactor_class))

	def process_info(self, info: Info):
		for reactor in self.reactors:
			try:
				reactor.react(info)
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('info_reactor_manager.react.error', type(reactor).__name__))

		# send command input from the console to the server's stdin
		if info.is_from_console and info.should_send_to_server():
			self.mcdr_server.send(info.content)

	def put_info(self, info):
		info.attach_mcdr_server(self.mcdr_server)
		# echo info from the server to the console
		if info.is_from_server:
			self.server_logger.info(info.raw_content)
		try:
			self.mcdr_server.task_executor.enqueue_info_task(lambda: self.process_info(info), info.is_user)
		except queue.Full:
			current_time = time.monotonic()
			logging_method = self.mcdr_server.logger.debug
			kwargs = {'option': DebugOption.REACTOR}
			if self.last_queue_full_warn_time is None or current_time - self.last_queue_full_warn_time >= core_constant.REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC:
				logging_method = self.mcdr_server.logger.warning
				kwargs = {}
				self.last_queue_full_warn_time = current_time
			logging_method(self.mcdr_server.tr('info_reactor_manager.info_queue.full'), **kwargs)

	def on_server_start(self):
		for reactor in self.reactors:
			reactor.on_server_start()

	def on_server_stop(self):
		for reactor in self.reactors:
			reactor.on_server_stop()
