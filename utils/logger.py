# -*- coding: utf-8 -*-

import logging
import sys
from logging.handlers import TimedRotatingFileHandler


class Logger:
	console_fmt = logging.Formatter('[%(name)s] [%(asctime)s %(threadName)s/%(levelname)s]: %(message)s', datefmt='%H:%M:%S')
	file_fmt = logging.Formatter('[%(name)s] [%(asctime)s %(threadName)s/%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

	def __init__(self, name=None):
		self.logger = logging.getLogger(name)
		self.file_handler = None

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(self.console_fmt)

		self.logger.addHandler(console_handler)
		self.logger.setLevel(logging.INFO)

		self.log = self.logger.log
		self.debug = self.logger.debug
		self.info = self.logger.info
		self.warning = self.logger.warning
		self.critical = self.logger.critical
		self.error = self.logger.error
		self.set_level = self.logger.setLevel

	def set_file(self, file_name):
		if self.file_handler is not None:
			self.logger.removeHandler(self.file_handler)
		self.file_handler = logging.handlers.TimedRotatingFileHandler(file_name, when='D', interval=1, backupCount=10)
		self.file_handler.setFormatter(self.file_fmt)
		self.logger.addHandler(self.file_handler)
