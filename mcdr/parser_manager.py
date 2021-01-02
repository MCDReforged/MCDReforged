import os

from ruamel import yaml

from mcdr import constant
from mcdr.parser.abstract_parser import AbstractParser
from mcdr.utils import misc_util


class ParserManager:
	def __init__(self, server, parser_folder):
		self.server = server
		self.parser_folder = parser_folder
		self.parser = AbstractParser(self)
		self.death_message_data = None
		self.death_message_dict = {}
		self.basic_parser = None

	def init(self):
		self.load_death_message_data()
		self.basic_parser = self.load_parser(constant.BASIC_PARSER_NAME)

	def load_parser(self, parser_name):
		"""
		Load a parser from the parser folder

		:param parser_name: the name of the parser you want to load
		:return: A parser instance inherited from AbstractParser
		:rtype: AbstractParser
		"""
		file_name = os.path.join(self.parser_folder, parser_name + constant.PARSER_FILE_SUFFIX)
		try:
			return misc_util.load_source(file_name).get_parser(self)
		except FileNotFoundError:
			self.server.logger.exception(self.server.tr('parser_manager.load_parser.file_not_found', parser_name))
			raise

	def install_parser(self, parser_name):
		self.parser = self.load_parser(parser_name)

	def update_death_message_list(self, cls):
		bases = misc_util.get_all_base_class(cls)
		names = [base.NAME for base in bases]
		result = []
		for name in names:
			try:
				result.extend(self.death_message_data[name])
			except:
				pass
		self.server.logger.debug('Search death message regular expressions for {} in {}, returned a list with length {}'.format(cls.NAME, ', '.join(names), len(result)))
		self.death_message_dict[cls] = result

	def get_stop_command(self):
		return self.parser.STOP_COMMAND

	def get_parser(self):
		return self.parser

	def get_basic_parser(self):
		return self.basic_parser

	def load_death_message_data(self):
		try:
			with open(constant.RE_DEATH_MESSAGE_FILE, 'r', encoding='utf8') as file:
				self.death_message_data = yaml.round_trip_load(file)
		except:
			self.server.logger.exception(self.server.tr('parser_manager.load_re_death_message.fail'))
			self.death_message_data = []

	# return a list of regular expression for death message matching
	# parameter cls is a parser class
	def get_death_message_list(self, cls):
		if cls not in self.death_message_dict:
			self.update_death_message_list(cls)
		return self.death_message_dict[cls]
