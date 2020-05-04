# -*- coding: utf-8 -*-

import logging
import os
import sys
import time
import zipfile
from colorlog import ColoredFormatter

from utils import tool


class NoColorFormatter(logging.Formatter):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def formatMessage(self, record):
		return tool.clean_console_color_code(super().formatMessage(record))


class Logger:
	console_fmt = ColoredFormatter(
		'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s',
		log_colors={
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'ERROR': 'bold_red',
			'CRITICAL': 'bold_red',
		},
		secondary_log_colors={
			'message': {
				'WARNING': 'yellow',
				'ERROR': 'red',
				'CRITICAL': 'red'
			}
		},
		datefmt='%H:%M:%S'
	)
	file_fmt = NoColorFormatter(
		'[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)

	def __init__(self, server, name=None):
		self.server = server
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
		self.exception = self.logger.exception
		self.set_level = self.logger.setLevel

	def set_file(self, file_name):
		if self.file_handler is not None:
			self.logger.removeHandler(self.file_handler)
		if not os.path.isdir(os.path.dirname(file_name)):
			os.makedirs(os.path.dirname(file_name))
		if os.path.isfile(file_name):
			modify_time = time.strftime('%Y-%m-%d', time.localtime(os.stat(file_name).st_mtime))
			counter = 0
			while True:
				counter += 1
				zip_file_name = '{}/{}-{}.zip'.format(os.path.dirname(file_name), modify_time, counter)
				if not os.path.isfile(zip_file_name):
					break
			zipf = zipfile.ZipFile(zip_file_name, 'w')
			zipf.write(file_name, arcname=os.path.basename(file_name), compress_type=zipfile.ZIP_DEFLATED)
			zipf.close()
			os.remove(file_name)
		self.file_handler = logging.FileHandler(file_name, encoding='utf8')
		self.file_handler.setFormatter(self.file_fmt)
		self.logger.addHandler(self.file_handler)
