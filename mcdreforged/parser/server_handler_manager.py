from logging import Logger
from typing import Dict, Optional

from mcdreforged.parser.abstract_server_handler import AbstractServerHandler
from mcdreforged.parser.impl.basic_handler import BasicHandler
from mcdreforged.parser.impl.beta18_handler import Beta18Handler
from mcdreforged.parser.impl.bukkit14_handler import Bukkit14Handler
from mcdreforged.parser.impl.bukkit_handler import BukkitHandler
from mcdreforged.parser.impl.bungeecord_handler import BungeecordHandler
from mcdreforged.parser.impl.cat_server_handler import CatServerHandler
from mcdreforged.parser.impl.forge_handler import ForgeHandler
from mcdreforged.parser.impl.vanilla_handler import VanillaHandler
from mcdreforged.parser.impl.waterfall_handler import WaterfallHandler


class ServerHandlerManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.handlers = {}  # type: Dict[str, AbstractServerHandler]
		self.__current_handler = None  # type: Optional[AbstractServerHandler]
		self.basic_parser = None  # TODO

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
			raise

	def get_current_handler(self) -> AbstractServerHandler:
		return self.__current_handler

	def get_basic_handler(self) -> AbstractServerHandler:
		return self.basic_parser
