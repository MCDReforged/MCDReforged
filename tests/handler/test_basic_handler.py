import unittest

from mcdreforged.handler.impl.basic_handler import BasicHandler

TEXT = '''
A quick example text
Another line for basic handler testing
Basic handler should work like a simple wrapper, 
that only adds time stamp and source information of the given text
'''.strip()


class MyTestCase(unittest.TestCase):
	def test_basic(self):
		parser = BasicHandler()
		self.assertEqual(parser.get_name(), 'basic_handler')
		for line in TEXT.splitlines():
			info = parser.parse_server_stdout(line)
			self.assertEqual(line, info.content)
			self.assertEqual(line, info.raw_content)
			self.assertEqual(False, info.is_from_console)
			self.assertEqual(True, info.is_from_server)
			self.assertEqual(False, info.is_player)
			self.assertEqual(False, info.is_user)


if __name__ == '__main__':
	unittest.main()
