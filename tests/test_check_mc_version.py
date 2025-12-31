import unittest

# noinspection PyProtectedMember
from mcdreforged.handler.impl.abstract_minecraft_handler import _check_mc_version_ge


class TestCheckMCVersionGE(unittest.TestCase):
	def test_check_mc_version_ge(self):
		test_cases = [
			("1.21", (1, 21, 0), (24, 1), True),
			("1.21.0", (1, 21, 0), (24, 1), True),
			("1.21.1", (1, 21, 0), (24, 1), True),
			("1.20.6", (1, 21, 0), (24, 1), False),
			("1.21", (1, 20, 0), (24, 1), True),
			("26.1", (1, 21, 0), (24, 1), True),
			("1.21.2", (1, 21, 1), (24, 1), True),
			("1.21", (1, 21, 1), (24, 1), False),
			("2.0", (1, 99, 0), (24, 1), True),
			("1.9", (1, 10, 0), (24, 1), False),
			("1.10", (1, 10, 0), (24, 1), True),
			("1.21", (1, 21), (24, 1), True),
			("1.21.0", (1, 21), (24, 1), True),
			("1.20.9", (1, 21), (24, 1), False),
			("1.21.1", (1, 21, 1), (24, 1), True),
			("1.21", (1, 21, 1), (24, 1), False),

			("1.21 pre-release 3", (1, 21, 0), (24, 1), True),
			("1.21 Pre-Release 3", (1, 21, 0), (24, 1), True),
			("1.21 release candidate 2", (1, 21, 0), (24, 1), True),
			("1.21 Release Candidate 2", (1, 21, 0), (24, 1), True),
			("1.20.5 Pre-Release 4", (1, 20, 5), (24, 1), True),
			("1.21 Release Candidate 1", (1, 21, 0), (24, 1), True),
			("1.20.6 Release Candidate 2", (1, 21, 0), (24, 1), False),
			("1.21.1 Pre-Release 1", (1, 21, 1), (24, 1), True),

			("22w45a", (1, 0, 0), (22, 45), True),
			("22w46a", (1, 0, 0), (22, 45), True),
			("23w14a", (1, 0, 0), (23, 10), True),
			("22w44a", (1, 0, 0), (22, 45), False),
			("21w50a", (1, 0, 0), (22, 45), False),
			("22W45A", (1, 0, 0), (22, 45), True),
			("100w01a", (1, 0, 0), (99, 50), True),
			("22w01a", (1, 0, 0), (22, 0), True),
			("22w00a", (1, 0, 0), (22, 1), False),
			("23w51a", (1, 0, 0), (24, 1), False),
			("24w01a", (1, 0, 0), (23, 52), True),
			("23w52a", (1, 0, 0), (24, 1), False),

			("24 Snapshot 1", (1, 0, 0), (24, 1), True),
			("24.1 Snapshot 10", (1, 0, 0), (24, 5), True),
			("24.2.3 Snapshot 2", (1, 0, 0), (24, 10), False),
			("25 Snapshot 1", (1, 0, 0), (24, 50), True),
			("24.0 Snapshot 1", (1, 0, 0), (24, 1), True),
			("24 Snapshot 2", (1, 0, 0), (24, 1), True),
			("24 Snapshot 0", (1, 0, 0), (24, 1), False),
			("24 snapshot 1", (1, 0, 0), (24, 1), True),
			("1 Snapshot 1", (1, 0, 0), (1, 1), True),
			("100.50.99 Snapshot 100", (1, 0, 0), (100, 50), True),

			(None, (1, 21, 0), (24, 1), False),
			("", (1, 21, 0), (24, 1), False),
			("invalid_version_abc", (1, 21, 0), (24, 1), False),
			("Combat Test 8", (1, 16, 0), (20, 1), False),
			("1.14.4", (1, 15, 0), (20, 1), False),
			("1.21 extra", (1, 21, 0), (24, 1), False),
			("22w45", (1, 0, 0), (22, 45), False),
			("24..1 Snapshot 1", (1, 0, 0), (24, 1), False),
			("24. Snapshot 1", (1, 0, 0), (24, 1), False),
			("24.1. Snapshot 1", (1, 0, 0), (24, 1), False),
			("1.21 Pre-Release", (1, 21, 0), (24, 1), False),
			("1.21 Release Candidate", (1, 21, 0), (24, 1), False),
			("1.21.1.1", (1, 21, 0), (24, 1), False),
		]

		for version_name, min_release, min_snapshot, expected in test_cases:
			with self.subTest(version_name=version_name, min_release=min_release, min_snapshot=min_snapshot):
				result = _check_mc_version_ge(version_name, min_release, min_snapshot)
				self.assertEqual(result, expected)


if __name__ == '__main__':
	unittest.main()
