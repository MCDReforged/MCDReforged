"""
Translation support
"""
from logging import Logger
from typing import Dict, Optional, Union

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext import RTextBase, RTextList
from mcdreforged.utils import resources_util

DEFAULT_LANGUAGE_RESOURCE_DIRECTORY = 'resources/lang/'


class TranslationManager:
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

	def translate(self, key: str, args: tuple, *, allow_failure: bool, fallback_translations: Optional[Dict[str, str]] = None) -> Union[str, RTextBase]:
		# Translating
		translated_text = self.translations.get(key)
		if translated_text is None and fallback_translations is not None:
			translated_text = fallback_translations.get(key)

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
				identifiers.append(args)
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
