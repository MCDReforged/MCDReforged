# -*- coding: utf-8 -*-

import ruamel.yaml as yaml
import os
from utils import tool


LANGUAGE_FILE_SUFFIX = '.yml'


class LanguageManager:
	def __init__(self, server, language_folder):
		self.server = server
		self.language_folder = language_folder
		self.language = None
		self.translations = {}

	def load_languages(self):
		self.translations = {}
		if os.path.isdir(self.language_folder):
			for file in tool.list_file(self.language_folder, LANGUAGE_FILE_SUFFIX):
				language = os.path.basename(file).rstrip(LANGUAGE_FILE_SUFFIX)
				with open(file, encoding='utf8') as f:
					self.translations[language] = yaml.round_trip_load(f)
			return True
		else:
			os.makedirs(self.language_folder)
			return False

	@property
	def languages(self):
		return self.translations.keys()

	def contain_language(self, language):
		return language in self.languages

	def translate(self, text, language=None):
		if language is None:
			language = self.language
		try:
			return self.translations[language][text]
		except:
			self.server.logger.error('Error translate text "{}" to language {}'.format(text, language))
			return text

	def set_language(self, language):
		self.language = language
