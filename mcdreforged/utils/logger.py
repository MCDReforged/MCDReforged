"""
Custom logger for MCDR
"""
import logging
import os
import sys
import time
import weakref
import zipfile
from contextlib import contextmanager
from enum import Enum, unique, auto
from threading import RLock, local
from typing import Dict, Optional, List, Set

from colorlog import ColoredFormatter

from mcdreforged.constants import core_constant
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


class SyncStdoutStreamHandler(logging.StreamHandler):
	__write_lock = RLock()
	__instance_lock = RLock()
	__instances = weakref.WeakSet()  # type: Set[SyncStdoutStreamHandler]

	def __init__(self):
		super().__init__(sys.stdout)
		with self.__instance_lock:
			self.__instances.add(self)

	def emit(self, record) -> None:
		with self.__write_lock:
			super().emit(record)

	@classmethod
	def update_stdout(cls, stream=None):
		if stream is None:
			stream = sys.stdout
		with cls.__instance_lock:
			instances = list(cls.__instances)
		for inst in instances:
			inst.acquire()  # use Handler's lock
			try:
				inst.stream = stream
			finally:
				inst.release()


class MCColoredFormatter(ColoredFormatter):
	MC_CODE_ITEMS = list(map(lambda item: item.value, list(RColor) + list(RStyle)))  # type: List[RItem]

	# global flag
	console_color_disabled = False

	__TLS = local()

	@classmethod
	@contextmanager
	def disable_minecraft_color_code_transform(cls):
		cls.__set_mc_code_trans_disable(True)
		try:
			yield
		finally:
			cls.__set_mc_code_trans_disable(False)

	@classmethod
	def __is_mc_code_trans_disabled(cls) -> bool:
		try:
			return cls.__TLS.mc_code_trans
		except AttributeError:
			cls.__set_mc_code_trans_disable(False)
			return False

	@classmethod
	def __set_mc_code_trans_disable(cls, state: bool):
		cls.__TLS.mc_code_trans = state

	def formatMessage(self, record):
		text = super().formatMessage(record)
		if not self.__is_mc_code_trans_disabled():
			# minecraft code -> console code
			for item in self.MC_CODE_ITEMS:
				if item.mc_code in text:
					text = text.replace(item.mc_code, item.console_code)
			# clean the rest of minecraft codes
			text = string_util.clean_minecraft_color_code(text)
		if self.console_color_disabled:
			text = string_util.clean_console_color_code(text)
		return text


class NoColorFormatter(logging.Formatter):
	def formatMessage(self, record):
		return string_util.clean_console_color_code(super().formatMessage(record))


class MCDReforgedLogger(logging.Logger):
	DEFAULT_NAME = core_constant.NAME_SHORT
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

		self.console_handler = SyncStdoutStreamHandler()
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

	def debug(self, *args, option: Optional[DebugOption] = None, no_check: bool = False):
		if no_check or self.should_log_debug(option):
			with MCColoredFormatter.disable_minecraft_color_code_transform():
				super().debug(*args)

	def set_file(self, file_name: str):
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

		console_handler = SyncStdoutStreamHandler()
		console_handler.setFormatter(self.server_fmt)

		self.addHandler(console_handler)
		self.setLevel(logging.DEBUG)
