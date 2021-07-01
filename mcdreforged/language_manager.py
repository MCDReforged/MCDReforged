"""
Translation support
"""
from logging import Logger
from typing import Dict, Optional

from mcdreforged.constants import core_constant
from mcdreforged.utils import resources_util

DEFAULT_LANGUAGE_RESOURCE_DIRECTORY = 'resources/lang/'


class LanguageManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.language = None
		self.translations = {}  # type: Dict[str, str]

	def set_language(self, language):
		self.language = language
		self.translations.clear()
		language_file_path = DEFAULT_LANGUAGE_RESOURCE_DIRECTORY + language + core_constant.LANGUAGE_FILE_SUFFIX
		try:
			self.translations = resources_util.get_yaml(language_file_path)
			if self.translations is None:
				raise FileNotFoundError('Language file not found')
			self.translations = dict(self.translations)
		except:
			self.logger.exception('Failed to load language {} from "{}"'.format(language, language_file_path))
		for key, value in self.translations.items():
			if not isinstance(key, str) or not isinstance(value, str):
				self.logger.error('Translation dict has illegal key-value, founded: {} ({}) - {} ({})'.format(key, type(key).__name__, value, type(value).__name__))

	def translate(self, key: str, allow_failure: bool, *, fallback_translations: Optional[Dict[str, str]] = None) -> str:
		# Translating
		translated_text = self.translations.get(key)
		if translated_text is None and fallback_translations is not None:
			translated_text = fallback_translations.get(key)

		# Processing
		if translated_text is not None:
			return translated_text
		else:
			if not allow_failure:
				raise KeyError('Translation key "{}" not found'.format(key))
			self.logger.error('Error translate text "{}" to current language {}'.format(key, self.language))
			return key
