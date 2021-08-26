import threading
from contextlib import contextmanager
from typing import Union, Iterable, Optional, List, Callable

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RTextBase, RAction, RStyle, RColor, RText
from mcdreforged.utils import translation_util


class RTextMCDRTranslation(RTextBase):
	__TLS = threading.local()
	__TLS.language = None
	__TLS.fallback_language = None

	def __init__(self, translation_key: str, *args, **kwargs):
		self.translation_key: str = translation_key
		self.args = args
		self.kwargs = kwargs
		self.__translator = lambda *args_, **kwargs_: RText(self.translation_key)
		self.__post_process: List[Callable[[RTextBase], RTextBase]] = []

		from mcdreforged.plugin.server_interface import ServerInterface
		server: Optional[ServerInterface] = ServerInterface.get_instance()
		if server is not None:
			self.set_translator(server.tr)

	def set_translator(self, translate_function: Callable) -> 'RTextMCDRTranslation':
		self.__translator = translate_function
		return self

	@classmethod
	def from_translation_dict(cls, translation_dict) -> 'RTextMCDRTranslation':
		def fake_tr(key: str, language: str):
			return translation_util.translate_from_dict(translation_dict, language)

		return RTextMCDRTranslation('').set_translator(fake_tr)

	def __get_translated_text(self) -> RTextBase:
		language = getattr(self.__TLS, 'language', None)
		if language is None:
			from mcdreforged.plugin.server_interface import ServerInterface
			server: Optional[ServerInterface] = ServerInterface.get_instance()
			if server is not None:
				language = server.get_mcdr_language()
			else:
				language = core_constant.DEFAULT_LANGUAGE
		processed_text = self.__translator(self.translation_key, *self.args, **self.kwargs, language=language)
		processed_text = RTextBase.from_any(processed_text)
		for process in self.__post_process:
			processed_text = process(processed_text)
		return processed_text

	@classmethod
	@contextmanager
	def language_context(cls, language: str):
		prev = getattr(cls.__TLS, 'language', None)
		cls.__TLS.language = language
		try:
			yield
		finally:
			cls.__TLS.language = prev

	def to_json_object(self) -> Union[dict, list]:
		return self.__get_translated_text().to_json_object()

	def to_plain_text(self) -> str:
		return self.__get_translated_text().to_plain_text()

	def to_colored_text(self) -> str:
		return self.__get_translated_text().to_colored_text()

	def copy(self) -> 'RTextBase':
		copied = RTextMCDRTranslation(self.translation_key, *self.args, **self.kwargs)
		copied.set_translator(self.__translator)
		return copied

	def set_color(self, color: RColor) -> 'RTextBase':
		self.__post_process.append(lambda rt: rt.set_color(color))
		return self

	def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> 'RTextBase':
		self.__post_process.append(lambda rt: rt.set_styles(styles))
		return self

	def set_click_event(self, action: RAction, value: str) -> 'RTextBase':
		self.__post_process.append(lambda rt: rt.set_click_event(action, value))
		return self

	def set_hover_text(self, *args) -> 'RTextBase':
		self.__post_process.append(lambda rt: rt.set_hover_text(*args))
		return self
