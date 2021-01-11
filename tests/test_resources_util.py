import unittest

from mcdreforged.config import DEFAULT_CONFIG_RESOURCE_PATH
from mcdreforged.utils import resources_util


class MyTestCase(unittest.TestCase):
	def test_get_config(self):
		self.assertIsNotNone(resources_util.get_data(DEFAULT_CONFIG_RESOURCE_PATH))
		data = resources_util.get_data('/' + DEFAULT_CONFIG_RESOURCE_PATH)
		self.assertIsNotNone(data)


if __name__ == '__main__':
	unittest.main()
