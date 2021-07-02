import logging
import unittest

from mcdreforged.translation_manager import TranslationManager


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.language_manager = TranslationManager(logging.getLogger())
		self.language_manager.load_translations()

	def test_0_same_key_order(self):
		language_key_dict = self.language_manager.translations
		language_list = list(language_key_dict.keys())
		base_lang = language_list[0]
		base_keys = list(language_key_dict[base_lang].keys())
		for test_lang, test_lang_mapping in language_key_dict.items():
			test_lang_keys = list(test_lang_mapping)
			for i, key in enumerate(base_keys):
				self.assertEqual(key, test_lang_keys[i], 'key[{}] "{}" in base language {} is not the same as test language {}'.format(i, key, base_lang, test_lang))
			self.assertEqual(len(base_keys), len(test_lang_keys))


if __name__ == '__main__':
	unittest.main()
