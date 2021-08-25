"""
Translation support
"""
import collections
import os
from logging import Logger
from typing import Optional, Set

from ruamel import yaml

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RTextBase
from mcdreforged.utils import file_util, translation_util
from mcdreforged.utils.logger import DebugOption
from mcdreforged.utils.types import TranslationStorage, MessageText

LANGUAGE_RESOURCE_DIRECTORY = os.path.join('resources', 'lang')
LANGUAGE_DIRECTORY = os.path.join(core_constant.PACKAGE_PATH, LANGUAGE_RESOURCE_DIRECTORY)


class TranslationManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.language = core_constant.DEFAULT_LANGUAGE
		self.translations: TranslationStorage = collections.defaultdict(dict)
		self.available_languages: Set[str] = set()

	def load_translations(self):
		self.translations.clear()
		self.available_languages.clear()
		for file_path in file_util.list_file_with_suffix(LANGUAGE_DIRECTORY, core_constant.LANGUAGE_FILE_SUFFIX):
			language, _ = os.path.basename(file_path).rsplit('.', 1)
			try:
				with open(os.path.join(LANGUAGE_DIRECTORY, file_path), encoding='utf8') as file_handler:
					translations = dict(yaml.load(file_handler, Loader=yaml.Loader))
				for key, text in translations.items():
					self.translations[key][language] = text
				self.available_languages.add(language)
				self.logger.debug('Loaded translation for {} with {} entries'.format(language, len(translations)), option=DebugOption.MCDR)
			except:
				self.logger.exception('Failed to load language {} from "{}"'.format(language, file_path))

	def set_language(self, language: str):
		self.language = language
		if language not in self.available_languages:
			self.logger.warning('Setting language to {} with 0 available translation'.format(language))

	def translate(self, key: str, args: tuple, kwargs: dict, *, allow_failure: bool, language: Optional[str] = None, fallback_language: Optional[str] = None, plugin_translations: Optional[TranslationStorage] = None) -> MessageText:
		if language is None:
			language = self.language
		if plugin_translations is None:
			plugin_translations = {}

		# Translating
		try:
			translated_text = translation_util.translate_from_dict(self.translations.get(key, {}), language, fallback_language=fallback_language)
		except KeyError:
			try:
				translated_text = translation_util.translate_from_dict(plugin_translations.get(key, {}), language, fallback_language=fallback_language, default=None)
			except KeyError:
				translated_text = None
		# Check if there's any rtext inside args
		use_rtext = False
		for arg in args:
			if isinstance(arg, RTextBase):
				use_rtext = True

		# Processing
		if translated_text is not None:
			translated_text = translated_text.strip('\n\r')
			try:
				if use_rtext:
					translated_text = RTextBase.format(translated_text, *args, **kwargs)
				else:
					translated_text = translated_text.format(*args, **kwargs)
			except Exception as e:
				raise ValueError('Failed to apply args {} and kwargs {} to translated_text {}: {}'.format(args, kwargs, translated_text, e))
			return translated_text
		else:
			if not allow_failure:
				raise KeyError('Translation key "{}" not found with language {}, fallback_language {}'.format(key, language, fallback_language))
			self.logger.error('Error translate text "{}" to language {}'.format(key, language))
			return key if not use_rtext else RTextBase.from_any(key)
