"""
Translation support
"""

import os

import ruamel.yaml as yaml

from mcdreforged import constant
from mcdreforged.utils import file_util, string_util


class LanguageManager:
	def __init__(self, mcdr_server, language_folder):
		self.mcdr_server = mcdr_server
		self.language_folder = language_folder
		self.language = None
		self.translations = {}

	def load_languages(self):
		self.translations = {}
		file_util.touch_folder(self.language_folder)
		for file in file_util.list_file_with_suffix(self.language_folder, constant.LANGUAGE_FILE_SUFFIX):
			language = string_util.remove_suffix(os.path.basename(file), constant.LANGUAGE_FILE_SUFFIX)
			with open(file, encoding='utf8') as f:
				self.translations[language] = yaml.round_trip_load(f)

	@property
	def languages(self):
		return self.translations.keys()

	def contain_language(self, language):
		return language in self.languages

	def translate(self, text, language=None) -> str:
		if language is None:
			language = self.language
		try:
			return self.translations[language][text]
		except:
			self.mcdr_server.logger.error('Error translate text "{}" to language {}'.format(text, language))
			return text

	def set_language(self, language):
		self.language = language
