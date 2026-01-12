import unittest

# noinspection PyProtectedMember
from mcdreforged.handler.impl.abstract_minecraft_handler import _check_mc_version_ge


class TestCheckMCVersionGE(unittest.TestCase):
	def test_check_mc_version_ge(self):
		min_release = (1, 21, 5)
		min_snapshot = (25, 3)  # 25w03a

		test_cases = [
			(None, False),
			("Unknown", False),

			("1.21.5", True),
			("1.21.6", True),
			("1.22", True),
			("1.22.0", True),
			("1.21.4", False),
			("1.21", False),
			("1.20.6", False),

			("1.21.5 Unobfuscated", True),
			("1.21.5 Pre-Release 1", True),
			("1.21.5 Release Candidate 2", True),
			("1.21.4 Release Candidate 1", False),
			("1.22 Pre-Release 1", True),

			("25w03a", True),
			("25w04a", True),
			("26w01a", True),
			("25w02a", False),
			("24w50a", False),
			("25w03b Unobfuscated", True),

			("25.0 Snapshot 3", True),
			("25.1 Snapshot 4", True),
			("26.0 Snapshot 1", True),
			("25.9 Snapshot 2", False),
		]

		for version_name, expected in test_cases:
			with self.subTest(version_name=version_name):
				result = _check_mc_version_ge(version_name, min_release, min_snapshot)
				self.assertEqual(
					result,
					expected,
					msg=f"Version '{version_name}' failed. Expected {expected}, got {result}"
				)


if __name__ == '__main__':
	unittest.main()
