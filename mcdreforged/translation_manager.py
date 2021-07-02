"""
Translation support
"""
import collections
import os
from logging import Logger
from typing import Dict, Optional, Union

from ruamel import yaml

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RTextBase, RTextList
from mcdreforged.utils import file_util
from mcdreforged.utils.logger import DebugOption

LANGUAGE_RESOURCE_DIRECTORY = os.path.join('resources', 'lang')
HERE = os.path.abspath(os.path.dirname(__file__))


class TranslationManager:
	def __init__(self, logger: Logger):
		self.logger = logger
		self.language = None
		self.translations = collections.defaultdict(dict)  # type: Dict[str, Dict[str, str]]

	def load_translations(self):
		language_directory = os.path.join(HERE, LANGUAGE_RESOURCE_DIRECTORY)
		for file_path in file_util.list_file_with_suffix(language_directory, core_constant.LANGUAGE_FILE_SUFFIX):
			language, _ = os.path.basename(file_path).rsplit('.', 1)
			try:
				with open(os.path.join(language_directory, file_path), encoding='utf8') as file_handler:
					translations = dict(yaml.load(file_handler, Loader=yaml.Loader))
				self.translations[language] = translations
				self.logger.debug('Loaded translation for {} with {} entries'.format(language, len(translations)), option=DebugOption.MCDR)
			except:
				self.logger.exception('Failed to load language {} from "{}"'.format(language, file_path))

	def set_language(self, language):
		self.language = language
		if len(self.translations[language]) == 0:
			self.logger.warning('Setting language to {} with 0 available translation'.format(language))

	def translate(self, key: str, args: tuple, *, allow_failure: bool, fallback_translations: Optional[Dict[str, Dict[str, str]]] = None) -> Union[str, RTextBase]:
		# Translating
		translated_text = self.translations[self.language].get(key)
		if translated_text is None and fallback_translations is not None:
			translated_text = fallback_translations.get(self.language, {}).get(key)

		# Check if there's any rtext inside args
		use_rtext = False
		for arg in args:
			if isinstance(arg, RTextBase):
				use_rtext = True

		# Processing
		if translated_text is not None:
			if use_rtext:
				return self.__apply_args(translated_text, args)
			else:
				if len(args) > 0:
					translated_text = translated_text.format(*args)
				return translated_text.strip('\n\r')
		else:
			if not allow_failure:
				raise KeyError('Translation key "{}" not found'.format(key))
			self.logger.error('Error translate text "{}" to current language {}'.format(key, self.language))
			return key if not use_rtext else RTextBase.from_any(key)

	@classmethod
	def __apply_args(cls, translated_text: str, args: tuple) -> RTextBase:
		identifiers = []
		for i, arg in enumerate(args):
			if isinstance(arg, RTextBase):
				identifiers.append('@@MCDR#Translation#Placeholder#{}@@'.format(i))
			else:
				identifiers.append(arg)
		texts = [translated_text.format(*identifiers)]
		for i, arg in enumerate(args):
			if isinstance(arg, RTextBase):
				new_texts = []
				for text in texts:
					processed_text = []
					if isinstance(text, str):
						for j, ele in enumerate(text.split(identifiers[i])):
							if j > 0:
								processed_text.append(arg)
							processed_text.append(ele)
					else:
						processed_text.append(text)
					new_texts.extend(processed_text)
				texts = new_texts
		return RTextList(*texts)
