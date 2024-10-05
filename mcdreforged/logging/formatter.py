import logging
from contextlib import contextmanager
from threading import local
from typing import List, Type

from colorlog import ColoredFormatter

from mcdreforged.minecraft.rtext.style import RItemClassic, RColor, RStyle
from mcdreforged.utils import string_utils


class MCColorFormatControl:
	MC_CODE_ITEMS: List[RItemClassic] = [item for item in list(RColor) + list(RStyle) if isinstance(item, RItemClassic)]
	assert all(item.mc_code.startswith('§') for item in MC_CODE_ITEMS), 'MC code items should start with §'

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
				text = string_utils.clean_minecraft_color_code(text)
		if cls.console_color_disabled:
			text = string_utils.clean_console_color_code(text)
		return text


class MCDReforgedFormatter(ColoredFormatter):
	def formatMessage(self, record: logging.LogRecord):
		text = super().formatMessage(record)
		return MCColorFormatControl.modify_message_text(text)


class NoColorFormatter(logging.Formatter):
	def formatMessage(self, record: logging.LogRecord):
		return string_utils.clean_console_color_code(super().formatMessage(record))


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
