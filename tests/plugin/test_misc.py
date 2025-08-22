import unittest

from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin


class PluginMiscTestCase(unittest.TestCase):
	def test_multi_file_plugin_check_dir_legality(self):
		pattern = MultiFilePlugin._ILLEGAL_ROOT_PY_FILE_STEM

		def assert_allowed(s: str):
			self.assertIsNone(pattern.fullmatch(s), 'assert_allowed() failed, pattern {} does not match {!r} (which should)'.format(pattern, s))

		def assert_illegal(s: str):
			self.assertIsNotNone(pattern.fullmatch(s), 'assert_illegal() failed, pattern {} matches {!r} (which should not)'.format(pattern, s))

		assert_allowed('__init__')
		assert_allowed('__main__')
		assert_allowed('__')
		assert_allowed('0abc')
		assert_allowed('Foo-Bar')
		assert_allowed('Foo+Bar')
		assert_allowed('.foo')
		assert_allowed('测试')

		assert_illegal('init')
		assert_illegal('main')
		assert_illegal('abc0')
		assert_illegal('Foo_Bar')
		assert_illegal('FooBar')
		assert_illegal('_foo')


if __name__ == '__main__':
	unittest.main()
