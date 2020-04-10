# -*- coding: utf-8 -*-
import os
import traceback

from ruamel import yaml

from utils import tool, constant


class ParserManager:
	def __init__(self, server):
		self.server = server
		self.parser = None
		self.death_message_data = None
		self.load_death_message_data()

	def load_parser(self, path, parser_name):
		file_name = os.path.join(path, parser_name + '.py')
		self.parser = tool.load_source(file_name).get_parser(self)

	def get_stop_command(self):
		return self.parser.STOP_COMMAND

	def get_parser(self):
		return self.parser

	def load_death_message_data(self):
		try:
			with open(constant.RE_DEATH_MESSAGE_FILE, 'r', encoding='utf8') as file:
				self.death_message_data = yaml.round_trip_load(file)
		except:
			self.server.logger.error(self.server.t('parser_manager.load_re_death_message.load_fail'))
			self.server.logger.error(traceback.format_exc())
			self.death_message_data = []

	# return a list of regular expression for death message matching
	# parameter cls is a parser class
	def get_death_message_list(self, cls):
		bases = tool.get_all_base_class(cls)
		names = [base.NAME for base in bases]
		self.server.logger.debug('Search death message regular expressions in {}'.format(', '.join(names)))
		result = []
		for name in names:
			try:
				result.extend(self.death_message_data[name])
			except:
				pass
		self.server.logger.debug('Returning a death message regular expressions list with length {}'.format(len(result)))
		return result
