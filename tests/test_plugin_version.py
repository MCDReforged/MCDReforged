import unittest

from mcdreforged.plugin.meta.version import *


class VersionTest(unittest.TestCase):
	def test_0_version_parsing(self):
		self.assertIsInstance(Version('1.0.0'), Version)
		self.assertIsInstance(Version('1.0.0-pre4'), Version)
		self.assertIsInstance(Version('1.0.0-pre.4'), Version)
		self.assertIsInstance(Version('1.998.0-'), Version)
		self.assertIsInstance(Version('1.998.0-alpha.100'), Version)
		self.assertIsInstance(Version('1.5.2-alpha.7+build10'), Version)
		self.assertIsInstance(Version('1.5.2-beta.100+build.2'), Version)
		self.assertIsInstance(Version('1.5.2--------w++++++++x'), Version)
		self.assertIsInstance(Version('0.0.0'), Version)
		self.assertIsInstance(Version('0.0.x'), Version)
		self.assertIsInstance(Version('0.x.*'), Version)
		self.assertIsInstance(Version('X.x.*'), Version)
		self.assertIsInstance(Version('X.x.*-QwQ.10+owo'), Version)
		self.assertIsInstance(Version('*'), Version)
		self.assertIsInstance(Version('*-alpha.x'), Version)
		self.assertIsInstance(Version('*-alpha.100'), Version)
		self.assertIsInstance(Version('*+b20'), Version)
		self.assertIsInstance(Version('1.2.0+20130313144700',), Version)
		self.assertIsInstance(Version('1.0.x'), Version)
		self.assertRaises(VersionParsingError, Version, '')
		self.assertRaises(VersionParsingError, Version, 'abc')
		self.assertRaises(VersionParsingError, Version, '0.-1.2')
		self.assertRaises(VersionParsingError, Version, '0..2')
		self.assertRaises(VersionParsingError, Version, '0.5.qwq')
		self.assertRaises(VersionParsingError, Version, '.2.3')
		self.assertRaises(VersionParsingError, Version, '1.2.')
		self.assertRaises(VersionParsingError, Version, '1.0.x', allow_wildcard=False)

	def test_1_compare(self):
		self.assertTrue(Version('1.2.3') == Version('1.2.3'))
		self.assertFalse(Version('1.2.3') < Version('1.2.3'))
		self.assertFalse(Version('1.2.3') > Version('1.2.3'))
		self.assertTrue(Version('1.2.3') >= Version('1.2.3'))
		self.assertTrue(Version('1.2.3') <= Version('1.2.3'))
		self.assertTrue(Version('1.2.3') <= Version('1.2.4'))
		self.assertTrue(Version('1.2.3') <= Version('1.3.3'))
		self.assertTrue(Version('1.2.3') < Version('1.3.3'))
		self.assertFalse(Version('1.2.3') == Version('1.3.3'))
		self.assertTrue(Version('1.2.3') != Version('1.3.3'))

		self.assertTrue(Version('1.2.3-alpha') < Version('1.2.3-beta'))
		self.assertTrue(Version('1.2.3-beta') < Version('1.2.3-beta.1'))
		self.assertTrue(Version('1.2.3-beta') < Version('1.2.3-beta.w'))
		self.assertTrue(Version('1.2.3-beta.1') < Version('1.2.3-beta.2'))
		self.assertTrue(Version('1.2.3-beta.9') < Version('1.2.3-beta.10'))
		self.assertTrue(Version('1.2.3-beta.100+build.1') == Version('1.2.3-beta.100+build.2'))

	def test_2_compare_wildcard(self):
		self.assertTrue(Version('1.2.3') >= Version('1.2.x'))
		self.assertFalse(Version('1.2.3') >= Version('1.3.x'))
		self.assertTrue(Version('1.2.3') >= Version('1.x'))
		self.assertTrue(Version('1.3.0') >= Version('1.3.x'))
		self.assertTrue(Version('1.3.0-pre1') >= Version('1.3.x'))
		self.assertTrue(Version('1.3.0-pre1') == Version('1.3.x+build2'))

	def test_3_version_requirement_parsing(self):
		self.assertIsInstance(VersionRequirement('>=1.0'), VersionRequirement)
		self.assertIsInstance(VersionRequirement('>=1.0 <2.0'), VersionRequirement)
		self.assertIsInstance(VersionRequirement('10'), VersionRequirement)
		self.assertIsInstance(VersionRequirement('1 2 3 4'), VersionRequirement)
		self.assertIsInstance(VersionRequirement('~1.2.3-pre.4+build.5.6'), VersionRequirement)
		self.assertIsInstance(VersionRequirement('<=2 >1 ~0'), VersionRequirement)
		self.assertRaises(VersionParsingError, VersionRequirement, 1234)
		self.assertRaises(VersionParsingError, VersionRequirement, '>')
		self.assertRaises(VersionParsingError, VersionRequirement, '<>1')
		self.assertRaises(VersionParsingError, VersionRequirement, '<=2 >1 ~0 ^')
		self.assertRaises(VersionParsingError, VersionRequirement, 'abc')

	def test_4_requirement_equal(self):
		for req in [VersionRequirement('1.4.0'), VersionRequirement('=1.4.0')]:
			self.assertTrue(req.accept('1.4.0'))
			self.assertTrue(req.accept('1.4.0+build2'))
			self.assertFalse(req.accept('1.4.1'))
			self.assertFalse(req.accept('1.4.0-pre.1'))
			self.assertFalse(req.accept('1.4.0-beta+build2'))

		req = VersionRequirement('1.4.x')
		self.assertTrue(req.accept('1.4.0'))
		self.assertTrue(req.accept('1.4.100'))
		self.assertTrue(req.accept('1.4.3-beta.10'))
		self.assertTrue(req.accept('1.4.3-beta.10+build.1.2.3.4'))
		self.assertTrue(req.accept('1.4.233-23333+abcd'))
		self.assertFalse(req.accept('1.3.0'))

		req = VersionRequirement('1.X')
		self.assertTrue(req.accept('1.4.0'))
		self.assertTrue(req.accept('1.4.100'))
		self.assertTrue(req.accept('1.4.3-beta.10'))
		self.assertTrue(req.accept('1.4.233-23333+abcd'))
		self.assertTrue(req.accept('1.3.0'))
		self.assertFalse(req.accept('2.0'))

	def test_5_requirement_less(self):
		req = VersionRequirement('<1.2.3')
		self.assertTrue(req.accept('1.2.3-'))
		self.assertTrue(req.accept('1.2.3-pre1'))
		self.assertTrue(req.accept('1.2.3-pre1+build1'))
		self.assertTrue(req.accept('1.2.2'))
		self.assertTrue(req.accept('1.1.4'))
		self.assertTrue(req.accept('0.0.0'))
		self.assertFalse(req.accept('1.2.3'))
		self.assertFalse(req.accept('1.2.3'))
		self.assertFalse(req.accept('1.2.4'))

		req = VersionRequirement('<1.x')
		self.assertTrue(req.accept('0.9'))
		self.assertTrue(req.accept('0.8.7.6'))
		self.assertFalse(req.accept('1.0.0'))
		self.assertFalse(req.accept('1.0-pre1'))

	def test_6_requirement_greater(self):
		req = VersionRequirement('>2.1.x')
		self.assertTrue(req.accept('2.2'))
		self.assertTrue(req.accept('2.2.2'))
		self.assertFalse(req.accept('2.1'))
		self.assertFalse(req.accept('2.1-pre1'))

		req = VersionRequirement('>2.1.x-pre.2')
		self.assertTrue(req.accept('2.2'))
		self.assertTrue(req.accept('2.2.2'))
		self.assertTrue(req.accept('2.1'))
		self.assertTrue(req.accept('2.1-pre.3'))
		self.assertFalse(req.accept('2.1-pre.1'))

		req = VersionRequirement('>=2.1.4-')
		self.assertTrue(req.accept('2.1.4'))
		self.assertTrue(req.accept('2.1.4-'))
		self.assertTrue(req.accept('2.1.4-alpha.3'))
		self.assertTrue(req.accept('2.1.4-rc1'))
		self.assertFalse(req.accept('2.1.3'))

	def test_7_requirement_range(self):
		req = VersionRequirement('>=1.2.0 <1.4.3')
		self.assertTrue(req.accept('1.2.1'))

	def test_8_requirement_other(self):
		req = VersionRequirement('^1.2.3-pre.5')
		self.assertTrue(req.accept('1.2.3-pre.5'))
		self.assertTrue(req.accept('1.2.3-pre.5-build.x'))
		self.assertTrue(req.accept('1.2.3-pre.6'))
		self.assertTrue(req.accept('1.2.3'))
		self.assertTrue(req.accept('1.100.0'))
		self.assertTrue(req.accept('1.3.0'))
		self.assertFalse(req.accept('1.2.2'))
		self.assertFalse(req.accept('1.2.3-pre.4'))
		self.assertFalse(req.accept('2.0.0'))

		req = VersionRequirement('~1.2.3-pre.5')
		self.assertTrue(req.accept('1.2.3-pre.5'))
		self.assertFalse(req.accept('1.100.0'))
		self.assertFalse(req.accept('1.2.2'))
		self.assertFalse(req.accept('1.2.3-pre.4'))
		self.assertFalse(req.accept('1.3.0'))
		self.assertFalse(req.accept('2.0.0'))

		req = VersionRequirement('*')
		self.assertTrue(req.accept('0.0.0'))
		self.assertTrue(req.accept('0-beta'))
		self.assertTrue(req.accept('1.0+build3'))
		self.assertTrue(req.accept('1.2.3'))

	def test_9_str(self):
		for version in (
			'1.0.0', '1.2.3-pre.5', '1.2.3-pre.qwq', '1.2.3-pre.5+build.x',
			'0', '1.1', '*', ('x', '*'), ('1.2.X', '1.2.*'), '43215.*-alpha.100'
		):
			if isinstance(version, tuple):
				version, expected = version
			else:
				expected = version
			self.assertEqual(expected, str(Version(version)))
			self.assertEqual(expected, str(VersionRequirement(version)))
		for req in (
			'>=1.0.0', '<=1.2.3-pre.5', '~1.2.3-pre.5-build.x',
			'>0', '^1.1.*',
		):
			self.assertEqual(req, str(VersionRequirement(req)))


if __name__ == '__main__':
	unittest.main()
