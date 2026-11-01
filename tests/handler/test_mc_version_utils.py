import unittest


class MyTestCase(unittest.TestCase):
	def __init__(self, *args):
		super().__init__(*args)

	def test_does_mc_version_has_execute_command(self):
		from mcdreforged.handler.impl.mc_version_utils import does_mc_version_has_execute_command

		self.assertFalse(does_mc_version_has_execute_command('blabla'))
		self.assertFalse(does_mc_version_has_execute_command('1.12'))
		self.assertFalse(does_mc_version_has_execute_command('1.12.3'))
		self.assertFalse(does_mc_version_has_execute_command('20'))
		self.assertFalse(does_mc_version_has_execute_command('1.17.x'))
		self.assertFalse(does_mc_version_has_execute_command('18w20a'))
		self.assertFalse(does_mc_version_has_execute_command('1.11 Pre-Release 12'))
		self.assertFalse(does_mc_version_has_execute_command('1.11.3 Release Candidate 1'))
		self.assertFalse(does_mc_version_has_execute_command('1.20.5 PreRelease 4'))
		self.assertFalse(does_mc_version_has_execute_command('Beta 1.8.1'))
		self.assertFalse(does_mc_version_has_execute_command('Beta 1.18.1'))

		self.assertTrue(does_mc_version_has_execute_command('1.13'))
		self.assertTrue(does_mc_version_has_execute_command('1.13.1'))
		self.assertTrue(does_mc_version_has_execute_command('1.17.1'))
		self.assertTrue(does_mc_version_has_execute_command('2.3'))
		self.assertTrue(does_mc_version_has_execute_command('2.3.4'))
		self.assertTrue(does_mc_version_has_execute_command('20.5'))
		self.assertTrue(does_mc_version_has_execute_command('123.456'))
		self.assertTrue(does_mc_version_has_execute_command('18w30a'))
		self.assertTrue(does_mc_version_has_execute_command('22w45a'))
		self.assertTrue(does_mc_version_has_execute_command('1.20'))
		self.assertTrue(does_mc_version_has_execute_command('1.20.5 Pre-Release 4'))
		self.assertTrue(does_mc_version_has_execute_command('1.19.4 pre-release 4'))
		self.assertTrue(does_mc_version_has_execute_command('1.21.1 Release Candidate 1'))
		self.assertTrue(does_mc_version_has_execute_command('1.21 release candidate 1'))


if __name__ == '__main__':
	unittest.main()
