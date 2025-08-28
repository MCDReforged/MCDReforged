import unittest

from mcdreforged.utils.string_utils import clean_console_color_code, clean_minecraft_color_code, hump_to_underline


class MyTestCase(unittest.TestCase):
	def test_0_clean_minecraft_color_code(self):
		self.assertEqual('fooo bar', clean_console_color_code('fooo bar'))
		self.assertEqual('\033m bar', clean_console_color_code('\033m bar'))
		self.assertEqual('\033[xm bar', clean_console_color_code('\033[xm bar'))
		self.assertEqual('\033[1;;m bar', clean_console_color_code('\033[1;;m bar'))
		self.assertEqual(' bar', clean_console_color_code('\033[m bar'))
		self.assertEqual('aa', clean_console_color_code('aa\x1b[7m'))
		self.assertEqual('bb', clean_console_color_code('bb\x1b[22m'))
		self.assertEqual('cc', clean_console_color_code('cc\x1b[23123;222m'))
		self.assertEqual('dd', clean_console_color_code('dd\x1b[1;23123;222m'))
		self.assertEqual('ee', clean_console_color_code('ee\x1b[38;2;255;255;85m'))

	def test_1_clean_minecraft_color_code(self):
		self.assertEqual('fooo bar', clean_minecraft_color_code('fooo bar'))
		self.assertEqual('bc', clean_minecraft_color_code('§abc'))
		self.assertEqual('§§zzzz7', clean_minecraft_color_code('§§§azz§bzz§77'))

	def test_2_hump_to_underline(self):
		self.assertEqual('the_other_class', hump_to_underline('TheOtherClass'))
		self.assertEqual('my_class', hump_to_underline('MyClass'))
		self.assertEqual('my_c1ass', hump_to_underline('MyC1ass'))
		self.assertEqual('abcd', hump_to_underline('ABCD'))
		self.assertEqual('abcd', hump_to_underline('abcd'))


if __name__ == '__main__':
	unittest.main()
