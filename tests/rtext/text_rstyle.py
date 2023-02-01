import unittest

from mcdreforged.api.rtext import *


class RTextColorTestCase(unittest.TestCase):
	def test_0_color_registry(self):
		self.assertIsInstance(RColor.red, RColor)
		self.assertIsInstance(RColor.green, RColor)
		self.assertIsInstance(RColor.reset, RColor)

	def test_1_color_create(self):
		self.assertIs(RColor.blue, RColor.from_mc_value('blue'))
		self.assertIs(RColor.yellow, RColor.from_mc_value('yellow'))
		self.assertIs(RColor.from_mc_value('aqua'), RColor.from_mc_value('aqua'))
		self.assertIsInstance(RColor.from_mc_value('#1579AF'), RColorRGB)
		self.assertIsInstance(RColor.from_mc_value('#1579AF'), RColorRGB)
		self.assertIsInstance(RColor.from_mc_value('1579AF'), RColorRGB)
		self.assertIsNot(RColor.from_mc_value('654321'), RColor.from_mc_value('654321'))

	def test_2_rgb_value(self):
		color = RColor.blue  # blue rgb hex: 0x5555FF
		self.assertIsInstance(color, RColorClassic)
		self.assertEqual(0x55, color.r)
		self.assertEqual(0x55, color.g)
		self.assertEqual(0xFF, color.b)

		color = RColor.from_mc_value('#1234FC')
		self.assertIsInstance(color, RColorRGB)
		self.assertEqual(0x12, color.r)
		self.assertEqual(0x34, color.g)
		self.assertEqual(0xFC, color.b)

	def test_3_rgb_convert(self):
		color = RColor.from_mc_value('#545454')
		self.assertIsInstance(color, RColorRGB)
		self.assertIsInstance(color.to_classic(), RColorClassic)
		self.assertIs(color.to_classic(), RColor.dark_gray)
		color.to_classic()

	def test_4_convert_cache(self):
		color = RColor.from_mc_value('dark_gray')
		self.assertIsInstance(color, RColorClassic)
		self.assertIs(color.to_rgb(), color.to_rgb())

		color = RColor.from_mc_value('#545454')
		self.assertIsInstance(color, RColorRGB)
		self.assertIs(color.to_classic(), color.to_classic())


class RTextStyleTestCase(unittest.TestCase):
	def test_0_style_registry(self):
		self.assertIsInstance(RStyle.bold, RStyle)
		self.assertIsInstance(RStyle.underlined, RStyle)
		self.assertIsInstance(RStyle.italic, RStyle)


if __name__ == '__main__':
	unittest.main()
