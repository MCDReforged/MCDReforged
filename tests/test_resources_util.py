import unittest

from mcdreforged.mcdr_config import MCDReforgedConfigManager
from mcdreforged.utils import resources_utils

DEFAULT_CONFIG_RESOURCE_PATH = MCDReforgedConfigManager.DEFAULT_CONFIG_RESOURCE_PATH


class MyTestCase(unittest.TestCase):
	def test_get_config(self):
		self.assertIsNotNone(resources_utils.get_data(DEFAULT_CONFIG_RESOURCE_PATH))
		data = resources_utils.get_data('/' + DEFAULT_CONFIG_RESOURCE_PATH)
		self.assertIsNotNone(data)


if __name__ == '__main__':
	unittest.main()
