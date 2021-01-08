from logging import Logger
from typing import Dict, Optional

from mcdreforged.parser.abstract_server_handler import AbstractServerHandler
from mcdreforged.parser.impl import *


class ServerHandlerManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.handlers = {}  # type: Dict[str, AbstractServerHandler]
		self.__current_handler = None  # type: Optional[AbstractServerHandler]
		self.basic_parser = None

	def register_handlers(self):
		self.basic_parser = BasicHandler()
		self.add_handler(self.basic_parser)
		self.add_handler(VanillaHandler())
		self.add_handler(BukkitHandler())
		self.add_handler(Bukkit14Handler())
		self.add_handler(ForgeHandler())
		self.add_handler(CatServerHandler())
		self.add_handler(Beta18Handler())
		self.add_handler(BungeecordHandler())
		self.add_handler(WaterfallHandler())

	def add_handler(self, parser: AbstractServerHandler):
		self.handlers[parser.get_name()] = parser

	def set_handler(self, parser_name: str):
		try:
			self.__current_handler = self.handlers[parser_name]
		except KeyError:
			self.logger.error('Fail to load parser with name "{}"'.format(parser_name))
			self.logger.error('Fallback basic parser is used, MCDR might not works correctly'.format(parser_name))
			self.__current_handler = self.basic_parser

	def get_current_handler(self) -> AbstractServerHandler:
		return self.__current_handler

	def get_basic_handler(self) -> AbstractServerHandler:
		return self.basic_parser
