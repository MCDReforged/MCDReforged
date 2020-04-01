# -*- coding: utf-8 -*-

from utils.parser.bungeecord_parser import BungeecordParser
from utils.parser.paper_parser import PaperParser


class WaterfallParser(PaperParser):
	STOP_COMMAND = 'end'

	@staticmethod
	def is_server_startup_done(info):
		return BungeecordParser.is_server_startup_done(info)


parser = WaterfallParser
