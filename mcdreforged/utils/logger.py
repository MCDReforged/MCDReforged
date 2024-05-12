"""
Custom logger for MCDR
"""
import datetime
import itertools
import logging
import os
import sys
import time
import zipfile
from contextlib import contextmanager
from enum import auto, Flag
from pathlib import Path
from threading import local, Lock
from typing import Dict, Optional, List, IO, Type

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


class ZippingDayRotatingFileHandler(logging.FileHandler):
	def __init__(self, file_path: str, rotate_day_count: int):
		self.rotate_day_count = rotate_day_count
		self.file_path = Path(file_path)
		self.dir_path = self.file_path.parent

		self.last_rover_date: Optional[datetime.date] = None
		self.last_record_date: Optional[datetime.date] = None
		self.try_rotate()

		super().__init__(file_path, encoding='utf8')

	def emit(self, record: logging.LogRecord) -> None:
		try:
			self.try_rotate()
			super().emit(record)
		except Exception:
			self.handleError(record)

	def try_rotate(self):
		current = datetime.datetime.now().date()

		if self.last_rover_date is None or (current - self.last_rover_date).days >= self.rotate_day_count:
			self.do_rotate(self.last_record_date and self.last_record_date.strftime('%Y-%m-%d'))
			self.last_rover_date = current

		self.last_record_date = current

	def do_rotate(self, base_name: Optional[str] = None):
		if not self.file_path.is_file():
			return

		inited = hasattr(self, 'stream')
		if inited:
			self.stream.close()
		try:
			if base_name is None:
				try:
					log_time = time.localtime(self.file_path.stat().st_mtime)
				except (OSError, OverflowError, ValueError):
					log_time = time.localtime()
				base_name = time.strftime('%Y-%m-%d', log_time)
			for counter in itertools.count(start=1):
				zip_path = self.dir_path / '{}-{}.zip'.format(base_name, counter)
				if not zip_path.is_file():
					break
			else:
				raise RuntimeError('should already able to get a valid zip path')
			with zipfile.ZipFile(zip_path, 'w') as zipf:
				zipf.write(self.file_path, arcname=self.file_path.name, compress_type=zipfile.ZIP_DEFLATED)

			try:
				self.file_path.unlink()
			except OSError:
				# failed to delete the old log file, might due to another MCDR instance being running
				# delete the rotated zip file to avoid duplication
				try:
					zip_path.unlink()
				except OSError:
					pass
				raise
		finally:
			if inited:
				self.stream = self._open()


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


class MCDReforgedFormatter(ColoredFormatter):
	def formatMessage(self, record: logging.LogRecord):
		text = super().formatMessage(record)
		return MCColorFormatControl.modify_message_text(text)


class NoColorFormatter(logging.Formatter):
	def formatMessage(self, record: logging.LogRecord):
		return string_util.clean_console_color_code(super().formatMessage(record))


class PluginIdAwareFormatter(logging.Formatter):
	PLUGIN_ID_KEY = 'plugin_id'

	def __init__(self, fmt_class: Type[logging.Formatter], fmt_str_with_key: str, **kwargs):
		super().__init__()
		fmt_str_without_key = fmt_str_with_key.replace(' [%(plugin_id)s]', '')
		if fmt_str_without_key == fmt_str_with_key:
			raise ValueError(fmt_str_with_key)

		self.fmt_with_key = fmt_class(fmt_str_with_key, **kwargs)
		self.fmt_without_key = fmt_class(fmt_str_without_key, **kwargs)

	def format(self, record: logging.LogRecord):
		if hasattr(record, self.PLUGIN_ID_KEY):
			return self.fmt_with_key.format(record)
		else:
			return self.fmt_without_key.format(record)


class MCDReforgedLogger(logging.Logger):
	DEFAULT_NAME = core_constant.NAME_SHORT
	ROTATE_DAY_COUNT = 7
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

	FILE_FORMATTER = PluginIdAwareFormatter(
		NoColorFormatter,
		f'[%(name)s] [%(asctime)s.%(msecs)d] [%(threadName)s/%(levelname)s] [%(filename)s:%(lineno)d(%(funcName)s)] [%(plugin_id)s]: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
	)
	CONSOLE_FORMATTER = PluginIdAwareFormatter(
		MCDReforgedFormatter,
		f'[%(name)s] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s] [%(plugin_id)s]: %(message_log_color)s%(message)s%(reset)s',
		log_colors=LOG_COLORS,
		secondary_log_colors=SECONDARY_LOG_COLORS,
		datefmt='%H:%M:%S',
	)

	debug_options: int = 0

	def __init__(self, plugin_id: Optional[str] = None):
		super().__init__(self.DEFAULT_NAME)
		self.file_handler: Optional[logging.FileHandler] = None
		self.__plugin_id = plugin_id

		self.console_handler = SyncStdoutStreamHandler()
		self.console_handler.setFormatter(self.CONSOLE_FORMATTER)

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

	def _log(self, *args, **kwargs) -> None:
		if self.__plugin_id is not None:
			extra_args = kwargs.get('extra', {})
			extra_args[PluginIdAwareFormatter.PLUGIN_ID_KEY] = self.__plugin_id
			kwargs['extra'] = extra_args

		# noinspection PyProtectedMember
		super()._log(*args, **kwargs)

	def debug(self, *args, option: Optional[DebugOption] = None, no_check: bool = False):
		if no_check or self.should_log_debug(option):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
				super().debug(*args, stacklevel=3)

	def set_file(self, file_path: str):
		"""
		**Not public API**

		:meta private:
		"""
		if self.file_handler is not None:
			self.unset_file()
		file_util.touch_directory(os.path.dirname(file_path))
		self.file_handler = ZippingDayRotatingFileHandler(file_path, self.ROTATE_DAY_COUNT)
		self.file_handler.setFormatter(self.FILE_FORMATTER)
		self.addHandler(self.file_handler)

	def unset_file(self):
		"""
		**Not public API**

		:meta private:
		"""
		if self.file_handler is not None:
			self.removeHandler(self.file_handler)
			self.file_handler.close()
			self.file_handler = None


class ServerOutputLogger:
	def __init__(self, name: str):
		self.name = name
		self.handler = SyncStdoutStreamHandler()

	def info(self, msg: str):
		msg = MCColorFormatControl.modify_message_text(msg)
		self.handler.write_direct('[{}] {}\n'.format(self.name, msg))
