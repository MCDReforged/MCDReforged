"""
Custom logger for MCDR
"""

import logging
import os
import sys
import time
import zipfile
from enum import Enum, unique, auto
from typing import Dict, Optional, List

from colorlog import ColoredFormatter

from mcdreforged import constant
from mcdreforged.minecraft.rtext import RColor, RStyle, RItem
from mcdreforged.utils import string_util, file_util


@unique
class DebugOption(Enum):
	# remember to sync with the debug field in the default config file
	ALL = auto()
	MCDR = auto()
	HANDLER = auto()
	REACTOR = auto()
	PLUGIN = auto()
	PERMISSION = auto()
	COMMAND = auto()
	TASK_EXECUTOR = auto()


# global flag
console_color_disabled = False


class MCColoredFormatter(ColoredFormatter):
	MC_CODE_ITEMS = list(map(lambda item: item.value, list(RColor) + list(RStyle)))  # type: List[RItem]

	def formatMessage(self, record):
		text = super().formatMessage(record)
		# minecraft code -> console code
		for item in self.MC_CODE_ITEMS:
			if item.mc_code in text:
				text = text.replace(item.mc_code, item.console_code)
		# clean the rest of minecraft codes
		text = string_util.clean_minecraft_color_code(text)
		if console_color_disabled:
			text = string_util.clean_console_color_code(text)
		return text


class NoColorFormatter(logging.Formatter):
	def formatMessage(self, record):
		return string_util.clean_console_color_code(super().formatMessage(record))


class MCDReforgedLogger(logging.Logger):
	DEFAULT_NAME = constant.NAME_SHORT
	LOG_COLORS = {
		'DEBUG': 'blue',
		'INFO': 'green',
		'WARNING': 'yellow',
		'ERROR': 'red',
		'CRITICAL': 'bold_red',
	}
	SECONDARY_LOG_COLORS = {
		'message': {
			'WARNING': 'yellow',
			'ERROR': 'red',
			'CRITICAL': 'red'
		}
	}
	FILE_FMT = NoColorFormatter(
		'[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)

	@classmethod
	def get_console_formatter(cls, plugin_id=None):
		extra = '' if plugin_id is None else ' [{}]'.format(plugin_id)
		return MCColoredFormatter(
			f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]{extra}: %(message_log_color)s%(message)s%(reset)s',
			log_colors=cls.LOG_COLORS,
			secondary_log_colors=cls.SECONDARY_LOG_COLORS,
			datefmt='%H:%M:%S'
		)

	debug_options = {}  # type: Dict[DebugOption, bool]

	def __init__(self, mcdr_server, plugin_id=None):
		super().__init__(self.DEFAULT_NAME)
		self.mcdr_server = mcdr_server
		self.file_handler = None

		self.console_handler = logging.StreamHandler(sys.stdout)
		self.console_handler.setFormatter(self.get_console_formatter(plugin_id))

		self.addHandler(self.console_handler)
		self.setLevel(logging.DEBUG)

	def set_debug_options(self, debug_options: Dict[str, bool]):
		for key, value in debug_options.items():
			option = DebugOption[key.upper()]
			MCDReforgedLogger.debug_options[option] = value
		for option, value in MCDReforgedLogger.debug_options.items():
			self.debug('Debug option {} is set to {}'.format(option, value), option=option)

	@classmethod
	def should_log_debug(cls, option: Optional[DebugOption] = None):
		do_log = cls.debug_options.get(DebugOption.ALL, False)
		if option is not None:
			do_log |= cls.debug_options.get(option, False)
		return do_log

	def debug(self, *args, option=None, no_check=False):
		if no_check or self.should_log_debug(option):
			super().debug(*args)

	def set_file(self, file_name):
		if self.file_handler is not None:
			self.removeHandler(self.file_handler)
		file_util.touch_directory(os.path.dirname(file_name))
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
		self.file_handler.setFormatter(self.FILE_FMT)
		self.addHandler(self.file_handler)


class ServerLogger(logging.Logger):
	server_fmt = MCColoredFormatter('[%(name)s] %(message)s')

	def __init__(self, name):
		super().__init__(name)

		console_handler = logging.StreamHandler(sys.stdout)
		console_handler.setFormatter(self.server_fmt)

		self.addHandler(console_handler)
		self.setLevel(logging.DEBUG)
