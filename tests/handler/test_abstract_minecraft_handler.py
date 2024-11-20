import unittest


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)

	def test_does_mc_version_has_execute_command(self):
		from mcdreforged.handler.impl.abstract_minecraft_handler import _does_mc_version_has_execute_command

		self.assertFalse(_does_mc_version_has_execute_command('blabla'))
		self.assertFalse(_does_mc_version_has_execute_command('1.12'))
		self.assertFalse(_does_mc_version_has_execute_command('1.12.3'))
		self.assertFalse(_does_mc_version_has_execute_command('20'))
		self.assertFalse(_does_mc_version_has_execute_command('1.17.x'))
		self.assertFalse(_does_mc_version_has_execute_command('18w20a'))
		self.assertFalse(_does_mc_version_has_execute_command('1.11 Pre-Release 12'))
		self.assertFalse(_does_mc_version_has_execute_command('1.11.3 Release Candidate 1'))
		self.assertFalse(_does_mc_version_has_execute_command('1.20.5 PreRelease 4'))
		self.assertFalse(_does_mc_version_has_execute_command('Beta 1.8.1'))
		self.assertFalse(_does_mc_version_has_execute_command('Beta 1.18.1'))

		self.assertTrue(_does_mc_version_has_execute_command('1.13'))
		self.assertTrue(_does_mc_version_has_execute_command('1.13.1'))
		self.assertTrue(_does_mc_version_has_execute_command('1.17.1'))
		self.assertTrue(_does_mc_version_has_execute_command('2.3'))
		self.assertTrue(_does_mc_version_has_execute_command('2.3.4'))
		self.assertTrue(_does_mc_version_has_execute_command('20.5'))
		self.assertTrue(_does_mc_version_has_execute_command('123.456'))
		self.assertTrue(_does_mc_version_has_execute_command('18w30a'))
		self.assertTrue(_does_mc_version_has_execute_command('22w45a'))
		self.assertTrue(_does_mc_version_has_execute_command('1.20'))
		self.assertTrue(_does_mc_version_has_execute_command('1.20.5 Pre-Release 4'))
		self.assertTrue(_does_mc_version_has_execute_command('1.19.4 pre-release 4'))
		self.assertTrue(_does_mc_version_has_execute_command('1.21.1 Release Candidate 1'))
		self.assertTrue(_does_mc_version_has_execute_command('1.21 release candidate 1'))


if __name__ == '__main__':
	unittest.main()
