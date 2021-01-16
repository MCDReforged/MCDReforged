import logging
import unittest

from mcdreforged.language_manager import LanguageManager


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)
		self.language_manager = LanguageManager(logging.getLogger())

	def test_0_same_key_order(self):
		language_list = ['en_us', 'zh_cn']
		language_key_dict = {}
		for lang in language_list:
			self.language_manager.set_language(lang)
			language_key_dict[lang] = list(self.language_manager.translations.keys())
		base_lang = language_list[0]
		base_keys = language_key_dict[base_lang]
		for test_lang, lang_keys in language_key_dict.items():
			for i, key in enumerate(base_keys):
				self.assertEqual(key, lang_keys[i], 'key[{}] "{}" in base language {} is not the same as test language {}'.format(i, key, base_lang, test_lang))
			self.assertEqual(len(base_keys), len(lang_keys))


if __name__ == '__main__':
	unittest.main()
