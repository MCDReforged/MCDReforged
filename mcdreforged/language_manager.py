"""
Translation support
"""
from logging import Logger
from typing import Dict

from mcdreforged import constant
from mcdreforged.utils import resources_util

DEFAULT_LANGUAGE_RESOURCE_FOLDER_PATH = 'resources/lang/'


class LanguageManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.language = None
		self.translations = {}  # type: Dict[str, str]

	def set_language(self, language):
		self.language = language
		self.translations.clear()
		language_file_path = DEFAULT_LANGUAGE_RESOURCE_FOLDER_PATH + language + constant.LANGUAGE_FILE_SUFFIX
		try:
			self.translations = resources_util.get_yaml(language_file_path)
			if self.translations is None:
				raise FileNotFoundError('Language file not found')
		except:
			self.logger.exception('Failed to load language {} from "{}"'.format(language, language_file_path))

	def translate(self, text) -> str:
		try:
			return self.translations[text]
		except:
			self.logger.error('Error translate text "{}" to current language {}'.format(text, self.language))
			return text
