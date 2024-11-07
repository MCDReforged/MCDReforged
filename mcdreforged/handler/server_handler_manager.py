import collections
import queue
import time
from logging import Logger
from typing import Dict, Optional, Tuple, List, TYPE_CHECKING, Counter

from mcdreforged.handler.impl import *
from mcdreforged.handler.plugin_provided_server_handler_holder import PluginProvidedServerHandlerHolder
from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.mcdr_config import MCDReforgedConfig
from mcdreforged.utils import misc_utils, class_utils

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class ServerHandlerManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger: Logger = mcdr_server.logger
		self.handlers: Dict[str, ServerHandler] = {}
		self.__tr = mcdr_server.create_internal_translator('server_handler_manager').tr

		self.__basic_handler: Optional[ServerHandler] = None  # the handler that should always work
		self.__plugin_provided_server_handler_holder: Optional[PluginProvidedServerHandlerHolder] = None
		self.__current_configured_handler_name: Optional[str] = None
		self.__current_configured_handler_invalid_warned: bool = False

		# Automation for lazy
		self.__handler_detector = HandlerDetector(self)

		mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, config: MCDReforgedConfig, log: bool):
		self.register_handlers(config.custom_handlers)
		self.set_configured_handler(config.handler)
		if log:
			self.logger.info(self.__tr('on_config_changed.handler_set', config.handler))

	def register_handlers(self, custom_handler_class_paths: Optional[List[str]]):
		def add_handler(hdr: ServerHandler):
			self.handlers[hdr.get_name()] = hdr

		self.handlers.clear()
		self.__basic_handler = BasicHandler()
		add_handler(self.__basic_handler)
		add_handler(VanillaHandler())
		add_handler(BukkitHandler())
		add_handler(Bukkit14Handler())
		add_handler(ForgeHandler())
		add_handler(CatServerHandler())
		add_handler(ArclightHandler())
		add_handler(Beta18Handler())
		add_handler(BungeecordHandler())
		add_handler(WaterfallHandler())
		add_handler(VelocityHandler())
		if custom_handler_class_paths is not None:
			for class_path in custom_handler_class_paths:
				try:
					handler_class = class_utils.load_class(class_path)
				except Exception:
					self.mcdr_server.logger.exception('Fail to load info handler from "{}"'.format(class_path))
				else:
					if issubclass(handler_class, ServerHandler):
						handler = handler_class()
						if handler.get_name() not in self.handlers:
							add_handler(handler)
							self.mcdr_server.logger.mdebug('Loaded info handler {} from {}'.format(handler_class.__name__, class_path), option=DebugOption.HANDLER)
						else:
							self.mcdr_server.logger.error('Handler with name {} from path {} is already registered, ignored'.format(handler.get_name(), class_path))
					else:
						self.mcdr_server.logger.error('Wrong handler class "{}", expected {} but found {}'.format(class_path, ServerHandler, handler_class))

	@property
	def __current_configured_handler(self) -> Optional[ServerHandler]:
		handler_name = self.__current_configured_handler_name
		try:
			return self.handlers[handler_name]
		except KeyError:
			if not self.__current_configured_handler_invalid_warned:
				self.logger.error('Fail to load configured handler with name {}'.format(repr(handler_name)))
				self.logger.error('Fallback basic handler is used, MCDR might not works correctly')
				self.__current_configured_handler_invalid_warned = True
			return self.__basic_handler

	def set_configured_handler(self, handler_name: str):
		if handler_name != self.__current_configured_handler_name:
			self.__shutdown_handler_detection()
		self.__current_configured_handler_name = handler_name
		self.__current_configured_handler_invalid_warned = False

	def set_plugin_provided_server_handler_holder(self, psh: Optional[PluginProvidedServerHandlerHolder]):
		if psh != self.__plugin_provided_server_handler_holder:
			if psh is not None:
				self.logger.info(self.__tr('plugin_provided.set', repr(psh.server_handler.get_name()), psh.plugin))
			else:
				self.logger.info(self.__tr('plugin_provided.unset', repr(self.__current_configured_handler.get_name())))
			self.__shutdown_handler_detection()
		self.__plugin_provided_server_handler_holder = psh

	def get_basic_handler(self) -> ServerHandler:
		return self.__basic_handler

	def get_plugin_provided_server_handler_holder(self) -> PluginProvidedServerHandlerHolder:
		return self.__plugin_provided_server_handler_holder

	def get_current_handler(self) -> ServerHandler:
		if (psh := self.__plugin_provided_server_handler_holder) is not None:
			return psh.server_handler
		return self.__current_configured_handler

	# Automation for lazy
	def start_handler_detection(self):
		self.__handler_detector.start_handler_detection()

	def __shutdown_handler_detection(self):
		self.__handler_detector.shutdown_handler_detection()

	def detect_text(self, text: str):
		self.__handler_detector.detect_text(text)


class HandlerDetector:
	HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT = 20   # At least 20 messages
	HANDLER_DETECTION_MINIMUM_SAMPLING_TIME = 60  # will do sample for 1 minute

	def __init__(self, manager: 'ServerHandlerManager'):
		self.manager = manager
		self.mcdr_server: 'MCDReforgedServer' = manager.mcdr_server
		self.running_flag = False
		self.text_queue: 'queue.Queue[Optional[str]]' = queue.Queue()
		self.text_count = 0
		self.success_count: Counter[str] = collections.Counter()
		self.__tr = self.mcdr_server.create_internal_translator('server_handler_manager').tr

	def start_handler_detection(self):
		if not self.is_detection_running():
			self.running_flag = True
			self.text_count = 0
			self.success_count.clear()
			misc_utils.start_thread(self.__detection_thread, (), 'HandlerDetector')

	def shutdown_handler_detection(self):
		# do nothing if it's called before the detection starts
		if self.is_detection_running():
			self.text_queue.put(None)

	def is_detection_running(self) -> bool:
		return self.running_flag

	def __detection_thread(self):
		start_time = time.time()
		try:
			while True:
				time_elapsed = time.time() - start_time
				if time_elapsed >= self.HANDLER_DETECTION_MINIMUM_SAMPLING_TIME and self.text_count >= self.HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT:
					break
				try:
					text = self.text_queue.get(block=True, timeout=1)
				except queue.Empty:
					continue
				if text is None:  # shutdown
					self.mcdr_server.logger.debug('Handler detection has shutdown')
					return

				self.text_count += 1
				handler: ServerHandler
				for handler in misc_utils.unique_list([*self.manager.handlers.values(), self.manager.get_current_handler()]):
					if handler is not self.manager.get_basic_handler():
						try:
							handler.parse_server_stdout(handler.pre_parse_server_stdout(text))
						except Exception:
							pass
						else:
							self.success_count[handler.get_name()] += 1
		finally:
			self.running_flag = False
			while True:  # drain the queue
				try:
					self.text_queue.get(block=False)
				except queue.Empty:
					break

		most_common: List[Tuple[str, int]] = self.success_count.most_common()
		if len(most_common) == 0:
			return
		total = self.text_count
		best_count = most_common[0][1]
		best_handler_tuples = [t for t in most_common if t[1] == best_count]
		best_handler_names = [t[0] for t in best_handler_tuples]

		current_handler = self.manager.get_current_handler()
		current_handler_name = current_handler.get_name()
		current_count = self.success_count[current_handler_name]

		if current_handler_name not in best_handler_names:
			psh = self.manager.get_plugin_provided_server_handler_holder()
			if psh is not None and current_handler is psh.server_handler:
				current_handler_name += ' ({})'.format(psh.plugin)

			self.mcdr_server.logger.warning(self.__tr('handler_detection.result1'))
			self.mcdr_server.logger.warning(self.__tr('handler_detection.result2', current_handler_name, round(100.0 * current_count / total, 2), current_count, total))
			for best_handler_name, best_count in best_handler_tuples:
				self.mcdr_server.logger.warning(self.__tr('handler_detection.result3', best_handler_name, round(100.0 * best_count / total, 2), best_count, total))

	def detect_text(self, text: str):
		if self.is_detection_running():
			self.text_queue.put(text)
