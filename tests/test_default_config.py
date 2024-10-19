import unittest

from ruamel.yaml import YAML

from mcdreforged.mcdr_config import MCDReforgedConfigManager, MCDReforgedConfig
from mcdreforged.utils import resources_utils

DEFAULT_CONFIG_RESOURCE_PATH = MCDReforgedConfigManager.DEFAULT_CONFIG_RESOURCE_PATH


class MyTestCase(unittest.TestCase):
	def setUp(self):
		self.maxDiff = None

	def test_default_config_consistency(self):
		self.assertIsNotNone(resources_utils.get_data(DEFAULT_CONFIG_RESOURCE_PATH))
		data = resources_utils.get_data('/' + DEFAULT_CONFIG_RESOURCE_PATH)
		self.assertIsNotNone(data)

		yaml_config = YAML(typ='safe').load(data)
		default_config = MCDReforgedConfig.get_default().serialize()

		# value equality
		self.assertIsInstance(default_config, dict)
		self.assertIsInstance(yaml_config, dict)
		self.assertEqual(default_config, yaml_config)

		# key order equality
		def check_keys(a: dict, b: dict, key_path: list):
			self.assertEqual(list(a.keys()), list(b.keys()), f'key_path={key_path}')
			for k, v in a.items():
				if isinstance(v, dict):
					check_keys(a[k], b[k], key_path + [k])

		check_keys(default_config, yaml_config, [])


if __name__ == '__main__':
	unittest.main()
