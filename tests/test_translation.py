import functools
import logging
import os
import unittest

from ruamel.yaml import YAML

from mcdreforged.constants import core_constant
from mcdreforged.minecraft.rtext.text import RText, RTextBase
from mcdreforged.translation.translation_manager import TranslationManager, MCDR_LANGUAGE_DIRECTORY
from mcdreforged.utils import file_utils


class MyTestCase(unittest.TestCase):
	translation_manager: TranslationManager

	def setUp(self) -> None:
		self.translation_manager = TranslationManager(logging.getLogger())

	def test_0_same_key_order(self):
		language_key_dict = {}
		for file_path in file_utils.list_file_with_suffix(MCDR_LANGUAGE_DIRECTORY, core_constant.LANGUAGE_FILE_SUFFIX):
			language, _ = os.path.basename(file_path).rsplit('.', 1)
			with open(os.path.join(MCDR_LANGUAGE_DIRECTORY, file_path), encoding='utf8') as file_handler:
				translations = dict(YAML().load(file_handler))
			language_key_dict[language] = translations

		language_list = list(language_key_dict.keys())
		base_lang = language_list[0]
		base_keys = list(language_key_dict[base_lang].keys())
		for test_lang, test_lang_mapping in language_key_dict.items():
			test_lang_keys = list(test_lang_mapping)
			for i, key in enumerate(base_keys):
				self.assertEqual(key, test_lang_keys[i], 'key[{}] "{}" in base language {} is not the same as test language {}'.format(i, key, base_lang, test_lang))
			self.assertEqual(len(base_keys), len(test_lang_keys))

	def test_1_translation_formatting(self):
		self.translation_manager.language = 'test_lang'
		self.translation_manager.translations['key1'] = {'test_lang': 'A {0} bb {c} {1}zzz'}
		tr = functools.partial(self.translation_manager.translate, allow_failure=False)

		self.assertEqual('A X bb Z Yzzz', tr('key1', ('X', 'Y'), {'c': 'Z'}))
		self.assertEqual('A X bb Z Yzzz', tr('key1', ('X', 'Y', 'dummy'), {'c': 'Z'}))
		self.assertEqual('A X bb Z Yzzz', tr('key1', ('X', 'Y'), {'c': 'Z', 'dummy': 'dummy'}))

		rtext = tr('key1', ('X', RText('Y')), {'c': 'Z'})
		self.assertIsInstance(rtext, RTextBase)
		self.assertEqual('A X bb Z Yzzz', rtext.to_plain_text())
		self.assertEqual(4, len(rtext.to_json_object()))

		rtext = tr('key1', ('X', RText('Y')), {'c': RText('Z')})
		self.assertIsInstance(rtext, RTextBase)
		self.assertEqual('A X bb Z Yzzz', rtext.to_plain_text())


if __name__ == '__main__':
	unittest.main()
