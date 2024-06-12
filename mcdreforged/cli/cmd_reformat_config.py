import sys
from typing import Optional

from ruamel.yaml import YAML

from mcdreforged.mcdr_config import MCDReforgedConfigManager
from mcdreforged.utils import resources_utils
from mcdreforged.utils.yaml_data_storage import YamlDataStorage


def reformat_config(input_path: str, output_path: Optional[str]):
	if output_path is None:
		output_path = input_path

	print('Reformatting configuration file {!r} to {!r}'.format(input_path, output_path))

	try:
		with open(input_path, 'r', encoding='utf8') as f:
			data = YAML(typ='safe').load(f)
	except FileNotFoundError:
		print('Input file {!r} does not exist'.format(input_path))
		sys.exit(1)
	except OSError as e:
		print('Failed to read input file {!r}: {}'.format(input_path, e))
		sys.exit(1)
	except ValueError as e:
		print('Failed to load yaml from file {!r}: {}'.format(input_path, e))
		sys.exit(1)

	new_data = resources_utils.get_yaml(MCDReforgedConfigManager.DEFAULT_CONFIG_RESOURCE_PATH)
	YamlDataStorage.merge_dict(data, new_data)

	try:
		with open(output_path, 'w', encoding='utf8') as f:
			yaml = YAML()
			yaml.width = 1048576  # prevent yaml breaks long string into multiple lines
			yaml.dump(new_data, f)
	except OSError as e:
		print('Failed to write output file {!r}: {}'.format(output_path, e))
		sys.exit(1)

	print('Reformatting completed')
