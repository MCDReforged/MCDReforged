import unittest
from typing import Iterable

from mcdreforged.constants import deprecations
from mcdreforged.plugin.meta.version import Version, VersionParsingError


class DeprecationTest(unittest.TestCase):
	@classmethod
	def iterate_deprecations(cls) -> Iterable[deprecations.Deprecation]:
		for name, value in vars(deprecations).items():
			if not name.startswith('_') and isinstance(value, deprecations.Deprecation):
				yield value

	def check_version(self, version_string: str):
		try:
			Version(version_string)
		except VersionParsingError as e:
			self.fail('bad version {}: {}'.format(repr(version_string), e))

	def test_deprecations(self):
		for d in self.iterate_deprecations():
			self.check_version(d.version_deprecated)
			self.check_version(d.version_removal)


if __name__ == '__main__':
	unittest.main()
