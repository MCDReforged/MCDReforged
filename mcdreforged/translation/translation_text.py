import threading
from contextlib import contextmanager
from typing import Union, Iterable, Optional, List, Callable, Any

from typing_extensions import Self, override, Unpack

from mcdreforged.minecraft.rtext.click_event import RClickEvent
from mcdreforged.minecraft.rtext.hover_event import RHoverEvent
from mcdreforged.minecraft.rtext.style import RColor, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.translation.functions import TranslateFunc
from mcdreforged.utils import translation_utils, class_utils, function_utils
from mcdreforged.utils.types.message import TranslationKeyDictRich


class RTextMCDRTranslation(RTextBase):
	"""
	The translation text component used in MCDR

	When MCDR is running, it will use the :meth:`~mcdreforged.plugin.si.server_interface.ServerInterface.tr` method
	in :class:`~mcdreforged.plugin.si.server_interface.ServerInterface` class as the translating method,
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
		self.__tr_func: TranslateFunc = function_utils.always(RText(self.translation_key))
		self.__post_process: List[Callable[[RTextBase], Any]] = []

		from mcdreforged.plugin.si.server_interface import ServerInterface
		server: Optional[ServerInterface] = ServerInterface.get_instance()
		if server is not None:
			self.set_translator(server.tr)

	def set_translator(self, translate_function: TranslateFunc) -> 'RTextMCDRTranslation':
		self.__tr_func = translate_function
		return self

	@classmethod
	def from_translation_dict(cls, translation_dict: TranslationKeyDictRich) -> 'RTextMCDRTranslation':
		def fake_tr(*_args, **_kwargs):
			return translation_utils.translate_from_dict(translation_dict, language=_kwargs['_mcdr_tr_language'])

		return RTextMCDRTranslation('').set_translator(fake_tr)

	def __get_translated_text(self) -> RTextBase:
		language = getattr(self.__TLS, 'language', None)
		if language is None:
			language = translation_utils.get_mcdr_language()
		processed_text = self.__tr_func(self.translation_key, *self.args, **self.kwargs, _mcdr_tr_language=language)
		processed_text = RTextBase.from_any(processed_text)
		for process in self.__post_process:
			process(processed_text)
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

	@override
	def to_json_object(self, **kwargs: Unpack[RTextBase.ToJsonKwargs]) -> Union[dict, list]:
		return self.__get_translated_text().to_json_object(**kwargs)

	@override
	def to_plain_text(self) -> str:
		return self.__get_translated_text().to_plain_text()

	@override
	def to_colored_text(self) -> str:
		return self.__get_translated_text().to_colored_text()

	@override
	def to_legacy_text(self) -> str:
		return self.__get_translated_text().to_legacy_text()

	@override
	def copy(self) -> 'RTextBase':
		copied = RTextMCDRTranslation(self.translation_key, *self.args, **self.kwargs)
		copied.__tr_func = self.__tr_func
		copied.__post_process = self.__post_process.copy()
		return copied

	@override
	def set_color(self, color: RColor) -> Self:
		def add_color(rt: RTextBase):
			return rt.set_color(color)
		self.__post_process.append(add_color)
		return self

	@override
	def set_styles(self, styles: Union[RStyle, Iterable[RStyle]]) -> Self:
		def set_styles(rt: RTextBase):
			return rt.set_styles(styles)
		self.__post_process.append(set_styles)
		return self

	@override
	def _set_click_event_direct(self, click_event: RClickEvent) -> Self:
		def set_click_event(rt: RTextBase):
			return rt._set_click_event_direct(click_event)
		self.__post_process.append(set_click_event)
		return self

	@override
	def set_hover_event(self, hover_event: RHoverEvent) -> Self:
		def set_hover_event(rt: RTextBase):
			return rt.set_hover_event(hover_event)
		self.__post_process.append(set_hover_event)
		return self

	@override
	def set_hover_text(self, *args) -> Self:
		def set_hover_text(rt: RTextBase):
			return rt.set_hover_text(*args)
		self.__post_process.append(set_hover_text)
		return self

	def __repr__(self) -> str:
		return class_utils.represent(self)

	def __eq__(self, other: 'RTextMCDRTranslation') -> bool:
		"""
		.. versionadded:: v2.15.0
		"""
		if type(other) != type(self):
			return False
		return self.__get_translated_text() == other.__get_translated_text()
