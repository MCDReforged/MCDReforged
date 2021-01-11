from logging import Logger
from typing import Dict, Optional

from mcdreforged.handler.abstract_server_handler import AbstractServerHandler
from mcdreforged.handler.impl import *


class ServerHandlerManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.handlers = {}  # type: Dict[str, AbstractServerHandler]
		self.__current_handler = None  # type: Optional[AbstractServerHandler]
		self.basic_handler = None

	def register_handlers(self):
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
