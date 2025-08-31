import os
import unittest
from typing import Dict, List, Optional, Union
from unittest.mock import patch

from typing_extensions import override

from mcdreforged.utils import misc_utils


class TestPrepareSubprocessEnvironment(unittest.TestCase):
	mock_environ = {'PATH': '/usr/bin', 'HOME': '/home/user'}

	@override
	def setUp(self):
		self.patcher = patch.dict(os.environ, self.mock_environ, clear=True)
		self.patcher.start()

	@override
	def tearDown(self):
		self.patcher.stop()

	def check(self, envs: Optional[Union[List[str], Dict[str, str]]], inherit: bool, expected: Optional[Dict[str, str]]):
		self.assertEqual(expected, misc_utils.prepare_subprocess_environment(envs, inherit))

	def test_none(self):
		self.check(None, True, None)
		self.check(None, False, {})

	def test_dict_envs(self):
		envs = {'KEY1': 'value1', 'KEY2': 'value2'}
		self.check(envs, True, {'PATH': '/usr/bin', 'HOME': '/home/user', 'KEY1': 'value1', 'KEY2': 'value2'})
		self.check(envs, False, {'KEY1': 'value1', 'KEY2': 'value2'})

		envs_override = {'PATH': '/new/path', 'NEW_KEY': 'new_value'}
		self.check(envs_override, True, {'PATH': '/new/path', 'HOME': '/home/user', 'NEW_KEY': 'new_value'})
		self.check(envs_override, False, {'PATH': '/new/path', 'NEW_KEY': 'new_value'})

	def test_list_envs(self):
		envs = ['KEY1=value1', 'KEY2=value2']
		self.check(envs, True, {'PATH': '/usr/bin', 'HOME': '/home/user', 'KEY1': 'value1', 'KEY2': 'value2'})
		self.check(envs, False, {'KEY1': 'value1', 'KEY2': 'value2'})

		envs_override = ['PATH=/new/path', 'NEW_KEY=new_value']
		self.check(envs_override, True, {'PATH': '/new/path', 'HOME': '/home/user', 'NEW_KEY': 'new_value'})
		self.check(envs_override, False, {'PATH': '/new/path', 'NEW_KEY': 'new_value'})

	def test_invalid_list_envs(self):
		envs = ['KEY1=value1', 'INVALID', 'KEY2=value2']
		self.check(envs, False, {'KEY1': 'value1', 'KEY2': 'value2'})
		self.check(envs, True, {'PATH': '/usr/bin', 'HOME': '/home/user', 'KEY1': 'value1', 'KEY2': 'value2'})

		envs_override = ['PATH=/new/path', 'INVALID', 'NEW_KEY=new_value']
		self.check(envs_override, True, {'PATH': '/new/path', 'HOME': '/home/user', 'NEW_KEY': 'new_value'})
		self.check(envs_override, False, {'PATH': '/new/path', 'NEW_KEY': 'new_value'})

	# noinspection PyTypeChecker
	def test_invalid_envs_type(self):
		with self.assertRaises(TypeError):
			misc_utils.prepare_subprocess_environment(123, False)
		with self.assertRaises(TypeError):
			misc_utils.prepare_subprocess_environment('123', True)

	def test_empty_dict_envs(self):
		envs: Dict[str, str] = {}
		self.check(envs, True, self.mock_environ)
		self.check(envs, False, {})

		envs_override = {'PATH': '/new/path', 'NEW_KEY': 'new_value'}
		self.check(envs_override, True, {'PATH': '/new/path', 'HOME': '/home/user', 'NEW_KEY': 'new_value'})
		self.check(envs_override, False, {'PATH': '/new/path', 'NEW_KEY': 'new_value'})

	def test_empty_list_envs(self):
		envs: List[str] = []
		self.check(envs, True, self.mock_environ)
		self.check(envs, False, {})

		envs_override = ['PATH=/new/path', 'NEW_KEY=new_value']
		self.check(envs_override, True, {'PATH': '/new/path', 'HOME': '/home/user', 'NEW_KEY': 'new_value'})
		self.check(envs_override, False, {'PATH': '/new/path', 'NEW_KEY': 'new_value'})


if __name__ == '__main__':
	unittest.main()
