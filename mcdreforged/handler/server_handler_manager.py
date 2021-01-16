import time
from typing import Dict, Optional, Tuple, List, TYPE_CHECKING

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.handler.impl import *
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import DebugOption

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class ServerHandlerManager:
	HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT = 20   # At least 20 messages
	HANDLER_DETECTION_MINIMUM_SAMPLING_TIME = 60  # will do sample for 1 minute

	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = mcdr_server.logger
		self.handlers = {}  # type: Dict[str, AbstractServerHandler]
		self.__current_handler = None  # type: Optional[AbstractServerHandler]
		self.basic_handler = None

		# Automation for lazy
		self.__detection_running = False
		self.__detection_start_time = None
		self.__detection_text_count = 0
		self.__detection_success_count = {}

	def register_handlers(self, custom_handler_class_paths: Optional[List[str]]):
		self.handlers.clear()
		self.basic_handler = BasicHandler()
		self.add_handler(self.basic_handler)
		self.add_handler(VanillaHandler())
		self.add_handler(BukkitHandler())
		self.add_handler(Bukkit14Handler())
		self.add_handler(ForgeHandler())
		self.add_handler(CatServerHandler())
		self.add_handler(Beta18Handler())
		self.add_handler(BungeecordHandler())
		self.add_handler(WaterfallHandler())
		if custom_handler_class_paths is not None:
			for class_path in custom_handler_class_paths:
				try:
					handler_class = misc_util.load_class(class_path)
				except:
					self.mcdr_server.logger.exception('Fail to load info handler from "{}"'.format(class_path))
				else:
					if issubclass(handler_class, AbstractServerHandler):
						handler = handler_class()
						if handler.get_name() not in self.handlers:
							self.add_handler(handler)
							self.mcdr_server.logger.debug('Loaded info handler {} from {}'.format(handler_class.__name__, class_path), option=DebugOption.HANDLER)
						else:
							self.mcdr_server.logger.error('Handler with name {} from path {} is already registered, ignored'.format(handler.get_name(), class_path))
					else:
						self.mcdr_server.logger.error('Wrong handler class "{}", expected {} but found {}'.format(class_path, AbstractServerHandler, handler_class))

	def add_handler(self, handler: AbstractServerHandler):
		self.handlers[handler.get_name()] = handler

	def set_handler(self, handler_name: str):
		try:
			self.__current_handler = self.handlers[handler_name]
		except KeyError:
			self.logger.error('Fail to load handler with name "{}"'.format(handler_name))
			self.logger.error('Fallback basic handler is used, MCDR might not works correctly'.format(handler_name))
			self.__current_handler = self.basic_handler

	def get_current_handler(self) -> AbstractServerHandler:
		return self.__current_handler

	def get_basic_handler(self) -> AbstractServerHandler:
		return self.basic_handler

	# Automation for lazy

	def start_handler_detection(self):
		if not self.is_detection_running():
			self.__detection_running = True
			self.__detection_text_count = 0
			self.__detection_success_count.clear()
			self.__detection_start_time = time.time()
			misc_util.start_thread(self.__detection_thread, (), 'HandlerDetector')

	def is_detection_running(self) -> bool:
		return self.__detection_running

	def __touch_detection_success_count(self, handler):
		if handler not in self.__detection_success_count:
			self.__detection_success_count[handler] = 0

	def __detection_thread(self):
		time.sleep(self.HANDLER_DETECTION_MINIMUM_SAMPLING_TIME)
		while self.__detection_text_count < self.HANDLER_DETECTION_MINIMUM_SAMPLE_COUNT:
			time.sleep(1)
		lst = self.finalize_detection_result()  # type: List[Tuple[AbstractServerHandler, int]]
		if len(lst) == 0:
			return
		total = self.__detection_text_count
		best_count = lst[0][1]
		end = 1
		while end < len(lst) and lst[end][1] == best_count:
			end += 1
		best_handlers = set(map(lambda item: item[0], lst[:end]))
		current_handler = self.get_current_handler()
		self.__touch_detection_success_count(current_handler)
		current_count = self.__detection_success_count[self.get_current_handler()]
		if current_handler not in best_handlers:
			self.mcdr_server.logger.warning(self.mcdr_server.tr('server_handler_manager.handler_detection.result1'))
			self.mcdr_server.logger.warning(self.mcdr_server.tr('server_handler_manager.handler_detection.result2', current_handler.get_name(), round(100.0 * current_count / total, 2), current_count, total))
			for best_handler, best_count in lst[:end]:
				self.mcdr_server.logger.warning(self.mcdr_server.tr('server_handler_manager.handler_detection.result3', best_handler.get_name(), round(100.0 * best_count / total, 2), best_count, total))

	def detect_text(self, text: str):
		if self.is_detection_running():
			self.__detection_text_count += 1
			for handler in self.handlers.values():
				if handler is not self.basic_handler:
					try:
						handler.parse_server_stdout(handler.pre_parse_server_stdout(text))
					except:
						pass
					else:
						self.__touch_detection_success_count(handler)
						self.__detection_success_count[handler] += 1

	def finalize_detection_result(self):
		self.__detection_running = False
		current_handler_set = set(self.handlers)
		lst = list(filter(lambda hdr: hdr in current_handler_set, self.__detection_success_count.items()))  # type: List[Tuple[AbstractServerHandler, int]]
		lst.sort(key=lambda item: item[1])
		lst.reverse()
		return lst
