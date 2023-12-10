import unittest

from colorama import Fore, Style

from mcdreforged.api.rtext import *


class RTextComponentTestCase(unittest.TestCase):
	def test_0_to_plain_text(self):
		self.assertEqual('foo', RText('foo').to_plain_text())
		self.assertEqual('foo', RText('foo', RColor.red).to_plain_text())
		self.assertEqual('foo', RText('foo', RColor.red, RStyle.bold).to_plain_text())

		text = RTextList('foo', RText('bar', RColor.yellow), 'baz')
		self.assertEqual('foobarbaz', text.to_plain_text())
		self.assertEqual('foobarbaz', text.set_color(RColor.blue).to_plain_text())
		self.assertEqual('foobarbaz', text.set_color(RColor.blue).set_styles(RStyle.italic).to_plain_text())

	def test_1_to_colored_text(self):
		self.assertEqual('foo', RText('foo').to_colored_text())
		self.assertEqual(Fore.LIGHTRED_EX + 'foo' + Style.RESET_ALL, RText('foo', RColor.red).to_colored_text())
		self.assertEqual(Fore.LIGHTRED_EX + Style.BRIGHT + 'foo' + Style.RESET_ALL, RText('foo', RColor.red, RStyle.bold).to_colored_text())

		text = RTextList('foo', RText('bar', RColor.yellow), 'baz')
		self.assertEqual(f'foo{Fore.LIGHTYELLOW_EX}bar{Style.RESET_ALL}baz', text.to_colored_text())
		s = ''.join([
			f'{Fore.LIGHTBLUE_EX}foo{Style.RESET_ALL}',
			f'{Fore.LIGHTBLUE_EX}{Fore.LIGHTYELLOW_EX}bar{Style.RESET_ALL}{Style.RESET_ALL}',
			f'{Fore.LIGHTBLUE_EX}baz{Style.RESET_ALL}',
		])
		self.assertEqual(s, text.set_color(RColor.blue).to_colored_text())
		self.assertEqual(s, text.set_color(RColor.blue).set_styles(RStyle.italic).to_colored_text())

	def test_2_to_legacy_text(self):
		self.assertEqual('foo', RText('foo').to_legacy_text())
		self.assertEqual('§c' + 'foo' + '§r', RText('foo', RColor.red).to_legacy_text())
		self.assertEqual('§c§l' + 'foo' + '§r', RText('foo', RColor.red, RStyle.bold).to_legacy_text())

		text = RTextList('foo', RText('bar', RColor.yellow), 'baz')
		self.assertEqual(''.join(['foo', '§e', 'bar', '§r', 'baz']), text.to_legacy_text())
		s = ''.join([
			'§9', 'foo', '§r',
			'§9§e', 'bar', '§r§r',
			'§9', 'baz', '§r',
		])
		self.assertEqual(s, text.set_color(RColor.blue).to_legacy_text())
		s = ''.join([
			'§9§o', 'foo', '§r',
			'§9§o§e', 'bar', '§r§r',
			'§9§o', 'baz', '§r',
		])
		self.assertEqual(s, text.set_color(RColor.blue).set_styles(RStyle.italic).to_legacy_text())


if __name__ == '__main__':
	unittest.main()