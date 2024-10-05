"""
Custom logger for MCDR
"""
import logging
import os
from typing import Dict, Optional, Any

from mcdreforged.constants import core_constant
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.file_handler import ZippingDayRotatingFileHandler
from mcdreforged.logging.formatter import MCColorFormatControl, MCDReforgedFormatter, NoColorFormatter, PluginIdAwareFormatter
from mcdreforged.logging.stream_handler import SyncStdoutStreamHandler
from mcdreforged.utils import file_utils


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
		self.setLevel(logging.INFO)

	def set_debug_options(self, debug_options: Dict[str, bool]):
		cls = type(self)
		cls.debug_options = 0
		for key, value in debug_options.items():
			if value:
				option = DebugOption[key.upper()]
				cls.debug_options |= option.mask
				self.mdebug('Debug option {} is set to {}'.format(option, value), option=option)

	@classmethod
	def should_log_debug(cls, option: Optional[DebugOption] = None):
		# noinspection PyTypeChecker
		flags: int = DebugOption.ALL.mask
		if option is not None:
			flags |= option.mask
		return (cls.debug_options & flags) != 0

	def _log(self, level: int, msg: Any, args: tuple, **kwargs) -> None:
		if self.__plugin_id is not None:
			extra_args = kwargs.get('extra', {})
			extra_args[PluginIdAwareFormatter.PLUGIN_ID_KEY] = self.__plugin_id
			kwargs['extra'] = extra_args

		# add 1 for this override
		# the default value 1 is from logging.Logger._log
		kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1

		# noinspection PyProtectedMember
		super()._log(level, msg, args, **kwargs)

	def mdebug(self, msg: Any, *args, option: Optional[DebugOption] = None, no_check: bool = False, stacklevel: int = 1):
		"""
		mcdr debug logging
		"""
		if no_check or self.isEnabledFor(logging.DEBUG) or self.should_log_debug(option):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
				self._log(logging.DEBUG, msg, args, stacklevel=stacklevel)

	def debug(self, msg: Any, *args, **kwargs):
		if self.isEnabledFor(logging.DEBUG) or self.should_log_debug(DebugOption.ALL):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
				self._log(logging.DEBUG, msg, args, **kwargs)

	def set_file(self, file_path: str):
		"""
		**Not public API**

		:meta private:
		"""
		if self.file_handler is not None:
			self.unset_file()
		file_utils.touch_directory(os.path.dirname(file_path))
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
