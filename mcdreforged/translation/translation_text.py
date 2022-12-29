import threading
from contextlib import contextmanager
from typing import Union, Iterable, Optional, List, Callable, TypeVar

from mcdreforged.minecraft.rtext.style import RColor, RStyle, RAction
from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.utils import translation_util
from mcdreforged.utils.types import TranslationKeyDictRich

Self = TypeVar('Self', bound='RTextMCDRTranslation')


class RTextMCDRTranslation(RTextBase):
	"""
	The translation text component used in MCDR

	When MCDR is running, it will use the :meth:`~mcdreforged.plugin.server_interface.ServerInterface.tr` method
	in :class:`~mcdreforged.plugin.server_interface.ServerInterface` class as the translating method,
	and the language of MCDR as the fallback translation language

	.. versionadded:: v2.1.0
	"""

	__TLS = threading.local()
	__TLS.language = None

	def __init__(self, translation_key: str, *args, **kwargs):
		"""
		Create a :class:`RTextMCDRTranslation` component with necessary parameters for translation

		:param translation_key: The translation key
		:param args: The translation arguments
		:param kwargs: The translation keyword arguments
		"""
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
	def from_translation_dict(cls, translation_dict: TranslationKeyDictRich) -> 'RTextMCDRTranslation':
		def fake_tr(_key: str, language: str):
			return translation_util.translate_from_dict(translation_dict, language)

		return RTextMCDRTranslation('').set_translator(fake_tr)

	def __get_translated_text(self) -> RTextBase:
		language = getattr(self.__TLS, 'language', None)
		if language is None:
			language = translation_util.get_mcdr_language()
		processed_text = self.__translator(self.translation_key, *self.args, **self.kwargs, language=language)
		processed_text = RTextBase.from_any(processed_text)
		for process in self.__post_process:
			processed_text = process(processed_text)
		return processed_text

	@classmethod
	@contextmanager
	def language_context(cls, language: str):
		"""
		Create a context where all :class:`RTextMCDRTranslation` will use the given language to translate within

		It's mostly used when you want a translated str or Minecraft json text object corresponding to this component under a specific language

		MCDR will automatically apply this context with :ref:`user's preferred language <preference-language>`
		right before sending messages to a player or the console

		Example::

			def log_message_line_by_line(server: ServerInterface):
				with RTextMCDRTranslation.language_context('en_us'):
					text: RTextMCDRTranslation = server.rtr('my_plugin.some_message')
					text_as_str: str = text.to_plain_text()  # The translation operation happens here
					server.logger.info('Lines of my translation')
					for line in text_as_str.splitlines():
						server.logger.info('- {}'.format(line))


		:param language: The language to be used during translation inside the context
		"""
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

	def set_color(self: Self, color: RColor) -> Self:
		self.__post_process.append(lambda rt: rt.set_color(color))
		return self

	def set_styles(self: Self, styles: Union[RStyle, Iterable[RStyle]]) -> Self:
		self.__post_process.append(lambda rt: rt.set_styles(styles))
		return self

	def set_click_event(self: Self, action: RAction, value: str) -> Self:
		self.__post_process.append(lambda rt: rt.set_click_event(action, value))
		return self

	def set_hover_text(self: Self, *args) -> Self:
		self.__post_process.append(lambda rt: rt.set_hover_text(*args))
		return self
