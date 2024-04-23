import unittest

from ruamel.yaml import YAML

from mcdreforged.mcdr_config import MCDReforgedConfigManager, MCDReforgedConfig
from mcdreforged.utils import resources_util

DEFAULT_CONFIG_RESOURCE_PATH = MCDReforgedConfigManager.DEFAULT_CONFIG_RESOURCE_PATH


class MyTestCase(unittest.TestCase):
	def test_default_config_consistency(self):
		self.assertIsNotNone(resources_util.get_data(DEFAULT_CONFIG_RESOURCE_PATH))
		data = resources_util.get_data('/' + DEFAULT_CONFIG_RESOURCE_PATH)
		self.assertIsNotNone(data)

		yaml_config = YAML(typ='safe').load(data)
		default_config = MCDReforgedConfig.get_default().serialize()
		self.assertEqual(default_config, yaml_config)


if __name__ == '__main__':
	unittest.main()
