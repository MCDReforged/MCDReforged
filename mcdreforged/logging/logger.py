"""
Custom logger for MCDR
"""
import functools
import logging
import os
import threading
from typing import Dict, Optional, Any, ClassVar, List, Type

from typing_extensions import override

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
		f'[{DEFAULT_NAME}] [%(asctime)s.%(msecs)03d] [%(threadName)s/%(levelname)s] [%(filename)s:%(lineno)d(%(funcName)s)] [%(plugin_id)s]: %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S',
	)
	CONSOLE_FORMATTER = PluginIdAwareFormatter(
		MCDReforgedFormatter,
		f'[{DEFAULT_NAME}] [%(asctime)s] [%(threadName)s/%(log_color)s%(levelname)s%(reset)s] [%(plugin_id)s]: %(message_log_color)s%(message)s%(reset)s',
		log_colors=LOG_COLORS,
		secondary_log_colors=SECONDARY_LOG_COLORS,
		datefmt='%H:%M:%S',
	)

	debug_options: ClassVar[int] = 0

	__file_handler_lock: ClassVar[threading.Lock] = threading.Lock()
	__file_handler_wanting_instances: ClassVar[List['MCDReforgedLogger']] = []
	__file_handler: ClassVar[Optional[ZippingDayRotatingFileHandler]] = None

	def __init__(self, name: str):
		super().__init__(name)
		self.setLevel(logging.INFO)

		self.console_handler = SyncStdoutStreamHandler()
		self.console_handler.setFormatter(self.CONSOLE_FORMATTER)
		self.addHandler(self.console_handler)

		with self.__file_handler_lock:
			if self.__file_handler is not None:
				self.addHandler(self.__file_handler)
			else:
				self.__file_handler_wanting_instances.append(self)

	__create_lock = threading.RLock()

	@classmethod
	@functools.lru_cache(None)
	def get(cls, plugin_id: Optional[str] = None) -> 'MCDReforgedLogger':
		"""
		**Not public API**

		:meta private:
		"""
		name = core_constant.PACKAGE_NAME
		if plugin_id:
			name += '-plugin-' + plugin_id
		with cls.__create_lock:
			prev_logger_class = logging.getLoggerClass()
			try:
				klass: Type[MCDReforgedLogger]
				if plugin_id is None:
					klass = MCDReforgedMainLogger
				else:
					klass = MCDReforgedPluginLogger
				logging.setLoggerClass(klass)
				logger = logging.getLogger(name)
				if not isinstance(logger, MCDReforgedLogger):
					raise TypeError('expected a logger with type {}, but got type {}'.format(klass, type(logger)))
				return logger
			finally:
				logging.setLoggerClass(prev_logger_class)

	@classmethod
	def _set_file(cls, file_path: str):
		"""
		**Not public API**

		:meta private:
		"""
		with cls.__file_handler_lock:
			if cls.__file_handler is not None:
				raise AssertionError('already set')

			file_utils.touch_directory(os.path.dirname(file_path))
			cls.__file_handler = ZippingDayRotatingFileHandler(file_path, cls.ROTATE_DAY_COUNT)
			cls.__file_handler.setFormatter(cls.FILE_FORMATTER)
			for inst in cls.__file_handler_wanting_instances:
				inst.addHandler(cls.__file_handler)
			cls.__file_handler_wanting_instances.clear()

	@classmethod
	def _get_file_handler(cls) -> Optional[ZippingDayRotatingFileHandler]:
		"""
		**Not public API**

		:meta private:
		"""
		return cls.__file_handler

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

	def mdebug(self, msg: Any, *args, option: Optional[DebugOption] = None, no_check: bool = False, stacklevel: int = 1):
		"""
		mcdr debug logging
		"""
		if no_check or self.isEnabledFor(logging.DEBUG) or self.should_log_debug(option):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
				self._log(logging.DEBUG, msg, args, stacklevel=stacklevel)

	@override
	def debug(self, msg: Any, *args, **kwargs):
		if self.isEnabledFor(logging.DEBUG) or self.should_log_debug(DebugOption.ALL):
			with MCColorFormatControl.disable_minecraft_color_code_transform():
				self._log(logging.DEBUG, msg, args, **kwargs)


class MCDReforgedMainLogger(MCDReforgedLogger):
	def __init__(self, name: str):
		if name != core_constant.PACKAGE_NAME:
			raise ValueError('Unexpected logger name {!r}'.format(name))
		super().__init__(name)


class MCDReforgedPluginLogger(MCDReforgedLogger):
	def __init__(self, name: str):
		# mcdreforged-plugin-${plugin_id}
		if name.startswith(prefix := core_constant.PACKAGE_NAME + '-plugin-'):
			plugin_id = name[len(prefix):]
		else:
			raise ValueError('Unexpected logger name {!r}'.format(name))

		super().__init__(name)
		self.__plugin_id = plugin_id

	def reset(self):
		self.setLevel(logging.INFO)

	@override
	def _log(self, level: int, msg: object, args: 'logging._ArgsType', *remaining_args, **kwargs) -> None:
		extra_args = kwargs.get('extra', {})
		extra_args[PluginIdAwareFormatter.PLUGIN_ID_KEY] = self.__plugin_id
		kwargs['extra'] = extra_args

		# add 1 for this override
		# the default value 1 is from logging.Logger._log
		kwargs['stacklevel'] = kwargs.get('stacklevel', 1) + 1

		super()._log(level, msg, args, *remaining_args, **kwargs)


class ServerOutputLogger:
	def __init__(self, name: str, mcdr_logger: MCDReforgedLogger):
		self.name = name
		self.handler = SyncStdoutStreamHandler()
		self.mcdr_logger = mcdr_logger

	def info(self, msg: str, *, write_to_mcdr_log_file: bool = False):
		msg = MCColorFormatControl.modify_message_text(msg)
		msg_line = '[{}] {}\n'.format(self.name, msg)
		self.handler.write_direct(msg_line)

		if write_to_mcdr_log_file:
			try:
				# noinspection PyProtectedMember
				if (fh := MCDReforgedLogger._get_file_handler()) is not None and fh.stream is not None:
					fh.stream.write(msg_line)
			except Exception as e:
				self.mcdr_logger.warning('write server output to mcdr log file failed: {}'.format(e))
