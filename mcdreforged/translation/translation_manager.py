"""
Translation support
"""
import collections
import os
from pathlib import Path
from typing import Optional, Set, TYPE_CHECKING

from ruamel.yaml import YAML

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext.text import RTextBase
from mcdreforged.utils import file_utils, translation_utils
from mcdreforged.utils.types.message import TranslationStorage, MessageText

if TYPE_CHECKING:
	from mcdreforged.logging.logger import MCDReforgedLogger

MCDR_LANGUAGE_DIRECTORY = Path(core_constant.PACKAGE_PATH) / 'resources' / 'lang'


class TranslationManager:
	def __init__(self, logger: 'MCDReforgedLogger'):
		self.logger = logger
		self.language = core_constant.DEFAULT_LANGUAGE
		self.translations: TranslationStorage = collections.defaultdict(dict)
		self.available_languages: Set[str] = set()

	def load_translations(self):
		self.translations.clear()
		self.available_languages.clear()
		for file_path in file_utils.list_file_with_suffix(MCDR_LANGUAGE_DIRECTORY, core_constant.LANGUAGE_FILE_SUFFIX):
			language, _ = os.path.basename(file_path).rsplit('.', 1)
			try:
				with open(os.path.join(MCDR_LANGUAGE_DIRECTORY, file_path), encoding='utf8') as file_handler:
					translations = dict(YAML().load(file_handler))
				for key, text in translation_utils.unpack_nest_translation(translations).items():
					self.translations[key][language] = text
				self.available_languages.add(language)
				self.logger.mdebug('Loaded translation for {} with {} entries'.format(language, len(translations)))
			except Exception:
				self.logger.exception('Failed to load language {} from "{}"'.format(language, file_path))

	def set_language(self, language: str):
		self.language = language
		if language not in self.available_languages:
			self.logger.warning('Setting language to {} with 0 available translation'.format(language))

	def translate(
			self,
			key: str, args: tuple, kwargs: dict,
			*,
			allow_failure: bool,
			language: Optional[str] = None,
			fallback_language: Optional[str] = None,
			plugin_translations: Optional[TranslationStorage] = None
	) -> MessageText:
		if language is None:
			language = self.language
		if plugin_translations is None:
			plugin_translations = {}

		# Translating
		try:
			translated_formatter = translation_utils.translate_from_dict(self.translations.get(key, {}), language, fallback_language=fallback_language)
		except KeyError:
			try:
				translated_formatter = translation_utils.translate_from_dict(plugin_translations.get(key, {}), language, fallback_language=fallback_language, default=None)
			except KeyError:
				translated_formatter = None

		# Check if there's any rtext inside args and kwargs
		use_rtext = any([isinstance(e, RTextBase) for e in list(args) + list(kwargs.values())])

		# Processing
		if translated_formatter is not None:
			translated_formatter = translated_formatter.strip('\n\r')
			try:
				if use_rtext:
					translated_formatter = RTextBase.format(translated_formatter, *args, **kwargs)
				else:
					translated_formatter = translated_formatter.format(*args, **kwargs)
			except Exception as e:
				raise ValueError('Failed to apply args {} and kwargs {} to translated_text {}: {}'.format(args, kwargs, translated_formatter, e))
			return translated_formatter
		else:
			if not allow_failure:
				raise KeyError('Translation key "{}" not found with language {}, fallback_language {}'.format(key, language, fallback_language))
			self.logger.error('Error translate text "{}" to language {}'.format(key, language))
			return key if not use_rtext else RTextBase.from_any(key)
