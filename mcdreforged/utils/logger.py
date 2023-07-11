"""
Custom logger for MCDR
"""
import logging
import os
import sys
import time
import zipfile
from contextlib import contextmanager
from enum import auto, Flag
from threading import local, Lock
from typing import Dict, Optional, List, IO

from colorlog import ColoredFormatter

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext.style import RColor, RStyle, RItemClassic
from mcdreforged.utils import string_util, file_util


class DebugOption(Flag):
	"""
	Remember to sync with the "debug" option in the default config file
	"""
	mask: int

	ALL = auto()
	MCDR = auto()
	HANDLER = auto()
	REACTOR = auto()
	PLUGIN = auto()
	PERMISSION = auto()
	COMMAND = auto()
	TASK_EXECUTOR = auto()


def __pre_fetch_debug_option_value():
	"""
	DebugOption.value call is more costly than simple attribute access
	"""
	for option in DebugOption:
		option.mask = option.value


__pre_fetch_debug_option_value()


class _SyncWriteStream:
	"""
	A stream wrapper with its method "write" synchronized.
	All accesses to other attributes are forwarded to the wrapped stream
	"""
	def __init__(self, stream: IO[str]):
		self.sws_stream = stream
		self.sws_lock = Lock()

	def write(self, s: str):
		with self.sws_lock:
			self.sws_stream.write(s)

	def __getattribute__(self, item: str):
		if item in ('write', 'sws_stream', 'sws_lock'):
			return object.__getattribute__(self, item)
		else:
			return self.sws_stream.__getattribute__(item)


class SyncStdoutStreamHandler(logging.StreamHandler):
	__sws = _SyncWriteStream(sys.stdout)

	def __init__(self):
		super().__init__(type(self).__sws)

	@classmethod
	def update_stdout(cls, stream: IO[str]):
		cls.__sws.sws_stream = stream

	@classmethod
	def write_direct(cls, s: str):
		cls.__sws.write(s)


class MCColorFormatControl:
	MC_CODE_ITEMS: List[RItemClassic] = list(filter(lambda item: isinstance(item, RItemClassic), list(RColor) + list(RStyle)))
	assert all(map(lambda item: item.mc_code.startswith('§'), MC_CODE_ITEMS)), 'MC code items should start with §'

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

	@classmethod
	def modify_message_text(cls, text: str) -> str:
		if not cls.__is_mc_code_trans_disabled():
			# minecraft code -> console code
			if '§' in text:
				for item in cls.MC_CODE_ITEMS:
					if item.mc_code in text:
						text = text.replace(item.mc_code, item.console_code)
				# clean the rest of minecraft codes
				text = string_util.clean_minecraft_color_code(text)
		if cls.console_color_disabled:
			text = string_util.clean_console_color_code(text)
		return text


class MCDReforgedFormatter(ColoredFormatter, MCColorFormatControl):
	def formatMessage(self, record):
		text = super().formatMessage(record)
		return self.modify_message_text(text)


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

	@property
	def __file_formatter(self):
		# it's not necessary to try to consider self.__plugin_id here
		# since the only FileHandler to be created is the in logger of the mcdr_server
		# which doesn't have the plugin id thing
		# for loggers for plugins, see mcdreforged.plugin.server_interface.ServerInterface._get_logger
		return NoColorFormatter(
			f'[%(name)s] [%(asctime)s] [%(threadName)s/%(levelname)s]: %(message)s',
			datefmt='%Y-%m-%d %H:%M:%S'
		)

	@property
	def __console_formatter(self):
		extra = '' if self.__plugin_id is None else ' [{}]'.format(self.__plugin_id)
		return MCDReforgedFormatter(
			f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s]{extra}: %(message_log_color)s%(message)s%(reset)s',
			log_colors=self.LOG_COLORS,
			secondary_log_colors=self.SECONDARY_LOG_COLORS,
			datefmt='%H:%M:%S'
		)

	debug_options: int = 0

	def __init__(self, plugin_id: Optional[str] = None):
		super().__init__(self.DEFAULT_NAME)
		self.file_handler: Optional[logging.FileHandler] = None
		self.__plugin_id = plugin_id

		self.console_handler = SyncStdoutStreamHandler()
		self.console_handler.setFormatter(self.__console_formatter)

		self.addHandler(self.console_handler)
		self.setLevel(logging.DEBUG)

	def set_debug_options(self, debug_options: Dict[str, bool]):
		cls = type(self)
		cls.debug_options = 0
		for key, value in debug_options.items():
			if value:
				option = DebugOption[key.upper()]
				cls.debug_options |= option.mask
				self.debug('Debug option {} is set to {}'.format(option, value), option=option)

	@classmethod
	def should_log_debug(cls, option: Optional[DebugOption] = None):
		# noinspection PyTypeChecker
		flags: int = DebugOption.ALL.mask
		if option is not None:
			flags |= option.mask
		return (cls.debug_options & flags) != 0

	def debug(self, *args, option: Optional[DebugOption] = None, no_check: bool = False):
		if no_check or self.should_log_debug(option):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
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
		self.file_handler.setFormatter(self.__file_formatter)
		self.addHandler(self.file_handler)

	def unset_file(self):
		if self.file_handler is not None:
			self.removeHandler(self.file_handler)
			self.file_handler.close()
			self.file_handler = None


class ServerOutputLogger:
	def __init__(self, name):
		self.name = name
		self.handler = SyncStdoutStreamHandler()

	def info(self, msg: str):
		msg = MCColorFormatControl.modify_message_text(msg)
		self.handler.write_direct('[{}] {}\n'.format(self.name, msg))
