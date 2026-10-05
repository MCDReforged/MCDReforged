import unittest

from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.exceptions import SpecifierParseError
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.specifier_hash_parser import SpecifierHashParser


class SpecifierHashParserTest(unittest.TestCase):
	def test_specifier_without_hash(self):
		for raw in ['my_plugin', 'my_plugin==1.2.3', 'my_plugin>=1.0', '', 'invalid requirement']:
			with self.subTest(raw=raw):
				# Requirement validation belongs to the caller.
				self.assertEqual((raw, None), SpecifierHashParser.parse_specifier(raw))

	def test_specifier_hash(self):
		specifier = 'my_plugin==1.2.3'
		for hash_hex in ['0123456789', 'ABCDEF0123', 'A' * 64]:
			for prefix in ['', 'sha256:', 'SHA256:']:
				raw = specifier + '@' + prefix + hash_hex
				with self.subTest(raw=raw):
					self.assertEqual((specifier, hash_hex.lower()), SpecifierHashParser.parse_specifier(raw))

	def test_specifier_hash_does_not_validate_requirement(self):
		for specifier in ['my_plugin>=1.0', 'invalid requirement']:
			for suffix in ['0123456789', 'sha256:0123456789']:
				raw = specifier + '@' + suffix
				with self.subTest(raw=raw):
					self.assertEqual((specifier, '0123456789'), SpecifierHashParser.parse_specifier(raw))

	def test_specifier_invalid_hash(self):
		for suffix in ['', 'a' * 9, 'a' * 65, 'abcdef012g', 'abcdef0123\n', 'abcdef0123@abcdef0123']:
			for prefix in ['', 'sha256:']:
				raw = 'my_plugin==1.2.3@' + prefix + suffix
				with self.subTest(raw=raw):
					self.assertRaises(SpecifierParseError, SpecifierHashParser.parse_specifier, raw)

	def test_specifier_unsupported_hash_method(self):
		for method in ['md5', 'SHA1']:
			raw = 'my_plugin==1.2.3@' + method + ':abcdef0123'
			with self.subTest(method=method):
				self.assertRaises(SpecifierParseError, SpecifierHashParser.parse_specifier, raw)

	def test_uri_without_hash(self):
		cases = [
			(True, 'https://example.com/plugin.mcdr'),
			(True, 'https://user:password@example.com/plugin.mcdr'),
			(True, 'https://user@example.com'),
			(True, 'https://user@example.com:443'),
			(True, 'https://user@[::1]:443/plugin.mcdr'),
			(True, 'https://example.com/plugins@release/plugin.mcdr'),
			(True, 'https://example.com/plugin.mcdr?email=user@example.com'),
			(True, 'https://example.com/plugin.mcdr#user@example.com'),
			(False, 'file://plugins/plugin.mcdr'),
			(False, 'file://plugins/plugin@release.mcdr'),
		]
		for is_remote, raw in cases:
			with self.subTest(raw=raw):
				self.assertEqual((raw, None), SpecifierHashParser.parse_uri(raw, is_remote=is_remote))

	def test_uri_hash(self):
		cases = [
			(True, 'https://example.com/plugin.mcdr'),
			(True, 'http://user:password@example.com:8080/plugins@release/plugin.mcdr'),
			(True, 'https://user@[::1]:443/plugin.mcdr'),
			(True, 'https://example.com'),
			(True, 'https://example.com/plugin.mcdr?token=abc#fragment'),
			(False, 'file://plugins/plugin.mcdr'),
			(False, 'file://plugins/plugin@release.mcdr'),
			(False, 'file://D:/plugins/plugin.mcdr'),
			(False, r'file://D:\plugins\plugin.mcdr'),
		]
		for is_remote, uri in cases:
			for hash_hex in ['ABCDEF0123', 'A' * 64]:
				raw = uri + '@SHA256:' + hash_hex
				with self.subTest(raw=raw):
					self.assertEqual((uri, hash_hex.lower()), SpecifierHashParser.parse_uri(raw, is_remote=is_remote))

	def test_uri_requires_explicit_hash_method(self):
		for is_remote, uri in [(True, 'https://example.com/plugin.mcdr'), (False, 'file://plugins/plugin.mcdr')]:
			raw = uri + '@abcdef0123'
			with self.subTest(raw=raw):
				self.assertEqual((raw, None), SpecifierHashParser.parse_uri(raw, is_remote=is_remote))

	def test_uri_hash_like_authority(self):
		# A host and port after user-info must not be consumed as a hash suffix.
		for raw in [
			'https://user@sha256:12345',
			'https://user@SHA256:443',
			'https://user@md5:443',
			'https://user@sha256:12345/plugin.mcdr',
			'https://user@md5:abcdef0123',
		]:
			with self.subTest(raw=raw):
				self.assertEqual((raw, None), SpecifierHashParser.parse_uri(raw, is_remote=True))

	def test_uri_hash_like_suffix_in_location(self):
		# These suffixes are part of the URI rather than a trailing hash validator.
		for suffix in [
			'sha256:abcdef0123/path',
			'sha256:abcdef0123?query=value',
			'sha256:abcdef0123#fragment',
			'sha256:abcdef0123@other',
		]:
			for is_remote, uri in [(True, 'https://example.com/plugin.mcdr'), (False, 'file://plugins/plugin.mcdr')]:
				raw = uri + '@' + suffix
				with self.subTest(raw=raw):
					self.assertEqual((raw, None), SpecifierHashParser.parse_uri(raw, is_remote=is_remote))

	def test_uri_invalid_hash(self):
		for is_remote, uri in [
			(True, 'https://example.com/plugin.mcdr'),
			(True, 'https://example.com'),
			(False, 'file://plugins/plugin.mcdr'),
		]:
			for hash_hex in ['', 'a' * 9, 'a' * 65, 'abcdef012g']:
				raw = uri + '@sha256:' + hash_hex
				with self.subTest(raw=raw):
					self.assertRaises(SpecifierParseError, SpecifierHashParser.parse_uri, raw, is_remote=is_remote)

	def test_uri_unsupported_hash_method(self):
		for is_remote, uri in [(True, 'https://example.com/plugin.mcdr'), (False, 'file://plugins/plugin.mcdr')]:
			for method, value in [('md5', 'abcdef0123'), ('SHA1', 'invalid')]:
				raw = uri + '@' + method + ':' + value
				with self.subTest(raw=raw):
					self.assertRaises(SpecifierParseError, SpecifierHashParser.parse_uri, raw, is_remote=is_remote)


if __name__ == '__main__':
	unittest.main()
