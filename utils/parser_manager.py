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
		self.death_message_list = {}
		self.load_death_message_data()

	def load_parser(self, path, parser_name):
		file_name = os.path.join(path, parser_name + '.py')
		self.parser = tool.load_source(file_name).get_parser(self)
		self.death_message_list.clear()
		self.update_death_message_list(type(self.parser))

	def update_death_message_list(self, cls):
		bases = tool.get_all_base_class(cls)
		names = [base.NAME for base in bases]
		result = []
		for name in names:
			try:
				result.extend(self.death_message_data[name])
			except:
				pass
		self.server.logger.debug('Search death message regular expressions for {} in {}, returned a list with length {}'.format(cls.NAME, ', '.join(names), len(result)))
		self.death_message_list[cls] = result

	def get_stop_command(self):
		return self.parser.STOP_COMMAND

	def get_parser(self):
		return self.parser

	def load_death_message_data(self):
		try:
			with open(constant.RE_DEATH_MESSAGE_FILE, 'r', encoding='utf8') as file:
				self.death_message_data = yaml.round_trip_load(file)
		except:
			self.server.logger.exception(self.server.t('parser_manager.load_re_death_message.fail'))
			self.death_message_data = []

	# return a list of regular expression for death message matching
	# parameter cls is a parser class
	def get_death_message_list(self, cls):
		if cls not in self.death_message_list:
			self.update_death_message_list(cls)
		return self.death_message_list[cls]
