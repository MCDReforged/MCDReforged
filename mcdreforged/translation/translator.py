from typing import TYPE_CHECKING

from typing_extensions import Protocol

from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.translation.translation_text import RTextMCDRTranslation


class TranslateFunc(Protocol):
	def __call__(self, key: str, *args, **kwargs) -> MessageText:
		...


class TranslateFuncR(Protocol):
	def __call__(self, key: str, *args, **kwargs) -> 'RTextMCDRTranslation':
		...


class Translator:
	def __init__(self, key_prefix: str, mcdr_server: 'MCDReforgedServer'):
		if key_prefix.startswith('.') or key_prefix.endswith('.'):
			raise ValueError(key_prefix)
		self.key_prefix = key_prefix
		self.__mcdr_server = mcdr_server

		from mcdreforged.translation.translation_text import RTextMCDRTranslation
		self.__rtr_cls = RTextMCDRTranslation
		self.tr: TranslateFunc = self.__tr
		self.rtr: TranslateFuncR = self

	def __real_tr(self, translation_key: str, *args, **kwargs) -> MessageText:
		return self.__mcdr_server.translate(translation_key, *args, **kwargs)

	def __tr(self, key: str, *args, **kwargs) -> MessageText:
		translation_key = self.key_prefix + '.' + key
		return self.__real_tr(translation_key, *args, **kwargs)

	def __call__(self, key: str, *args, **kwargs) -> 'RTextMCDRTranslation':
		translation_key = self.key_prefix + '.' + key
		text = self.__rtr_cls(translation_key, *args, **kwargs)
		text.set_translator(self.__real_tr)
		return text
