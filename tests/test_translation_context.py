import asyncio
import unittest

from mcdreforged.translation.translation_text import RTextMCDRTranslation


class TestTranslationContext(unittest.TestCase):
    def test_async_tasks_keep_language_context_isolated(self):
        translations = {'en_us': 'EN', 'zh_cn': 'ZH'}

        async def render(language):
            with RTextMCDRTranslation.language_context(language):
                await asyncio.sleep(0)
                return RTextMCDRTranslation.from_translation_dict(translations).to_plain_text()

        async def run():
            return await asyncio.gather(render('en_us'), render('zh_cn'))

        self.assertEqual(['EN', 'ZH'], asyncio.run(run()))

    def test_nested_context_restores_previous_language(self):
        translations = {'en_us': 'EN', 'zh_cn': 'ZH'}

        with RTextMCDRTranslation.language_context('en_us'):
            self.assertEqual('EN', RTextMCDRTranslation.from_translation_dict(translations).to_plain_text())
            with RTextMCDRTranslation.language_context('zh_cn'):
                self.assertEqual('ZH', RTextMCDRTranslation.from_translation_dict(translations).to_plain_text())
            self.assertEqual('EN', RTextMCDRTranslation.from_translation_dict(translations).to_plain_text())


if __name__ == '__main__':
    unittest.main()
