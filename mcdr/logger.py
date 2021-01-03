"""
Custom logger for MCDR
"""

import logging
import os
import sys
import time
import zipfile

from colorlog import ColoredFormatter

from mcdr.rtext import *
from mcdr.utils import string_util, file_util


class DebugOption:
	ALL = 'all'
	PARSER = 'parser'
	PLUGIN = 'plugin'


class MCColoredFormatter(ColoredFormatter):
	def formatMessage(self, record):
		text = super().formatMessage(record)
		text = RColor.convert_minecraft_color_code(text)  # minecraft code -> console code
		text = string_util.clean_minecraft_color_code(text)  # clean the rest of minecraft codes
		return text


class NoColorFormatter(logging.Formatter):
	def formatMessage(self, record):
		return string_util.clean_console_color_code(super().formatMessage(record))


class Logger:
	console_fmt = MCColoredFormatter(
		'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]: %(message_log_color)s%(message)s%(reset)s',
		log_colors={
			'DEBUG': 'blue',
			'INFO': 'green',
			'WARNING': 'yellow',
			'ERROR': 'red',
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

	def __init__(self, mcdr_server, name=None):
		self.mcdr_server = mcdr_server
		self.logger = logging.getLogger(name)
		self.file_handler = None

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(self.console_fmt)

		self.logger.addHandler(console_handler)
		self.logger.setLevel(logging.DEBUG)

		self.log = self.logger.log
		self.info = self.logger.info
		self.warning = self.logger.warning
		self.critical = self.logger.critical
		self.error = self.logger.error
		self.exception = self.logger.exception

		self.debug_options = {}

	def set_debug_options(self, debug_options: dict):
		self.debug_options = debug_options
		for key, value in debug_options.items():
			self.logger.debug('Debug option {} is set to {}'.format(key, value))

	def debug(self, *args, option=None):
		do_log = self.debug_options.get(DebugOption.ALL, False)
		if option is not None:
			do_log |= self.debug_options.get(option, False)
		if do_log:
			self.logger.debug(*args)

	@property
	def level(self):
		return self.logger.level

	def set_file(self, file_name):
		if self.file_handler is not None:
			self.logger.removeHandler(self.file_handler)
		file_util.touch_folder(os.path.dirname(file_name))
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


class ServerLogger(logging.Logger):
	server_fmt = MCColoredFormatter('[%(name)s] %(message)s')

	def __init__(self, name):
		super().__init__(name)

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(self.server_fmt)

		self.addHandler(console_handler)
		self.setLevel(logging.DEBUG)
