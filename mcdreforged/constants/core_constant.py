"""
Core constants
"""

import os
from pathlib import Path

# will be modified in CI
__CI_BUILD_NUM = None

NAME_SHORT = 'MCDR'
NAME = 'MCDReforged'
PACKAGE_NAME = 'mcdreforged'
CLI_COMMAND = PACKAGE_NAME

# MCDR Version Storage
VERSION = '2.13.2'       # semver (1.2.3-alpha.4)
VERSION_PYPI = '2.13.2'  # pythonic ver (1.2.3a4)

GITHUB_URL = 'https://github.com/MCDReforged/MCDReforged'
GITHUB_API_LATEST_URLS = [
	'https://api.mcdreforged.com/releases/latest',
	'https://api.github.com/repos/MCDReforged/MCDReforged/releases/latest',
]
DOCUMENTATION_URL = 'https://docs.mcdreforged.com'
PLUGIN_CATALOGUE_META_URL = 'https://api.mcdreforged.com/catalogue/everything_slim.json.xz'

PACKAGE_PATH = Path(__file__).absolute().parent.parent  # path of the mcdreforged directory
LOGGING_FILE = os.path.join('logs', '{}.log'.format(NAME_SHORT))
LANGUAGE_FILE_SUFFIX = '.yml'
DEFAULT_LANGUAGE = 'en_us'

CONFIG_FILE_PATH = 'config.yml'
PERMISSION_FILE_PATH = 'permission.yml'

PLUGIN_THREAD_POOL_SIZE = 4
MAX_TASK_QUEUE_SIZE = 2048
WAIT_TIME_AFTER_SERVER_STDOUT_END_SEC = 60
REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC = 5


if isinstance(__CI_BUILD_NUM, str) and __CI_BUILD_NUM.isdigit():
	VERSION += '+dev.{}'.format(__CI_BUILD_NUM)
	VERSION_PYPI += '.dev{}'.format(__CI_BUILD_NUM)
