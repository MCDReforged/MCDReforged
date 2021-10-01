"""
Core constants
"""

import os


NAME_SHORT = 'MCDR'
NAME = 'MCDReforged'
PACKAGE_NAME = 'mcdreforged'

# MCDR Version Storage
# Related: docs/source/conf.py
VERSION = '2.2.1'       # semver (1.2.3-alpha.4)
VERSION_PYPI = '2.2.1'  # pythonic ver (1.2.3a4)

GITHUB_URL = 'https://github.com/Fallen-Breath/MCDReforged'
GITHUB_API_LATEST = 'https://api.github.com/repos/Fallen-Breath/MCDReforged/releases/latest'

PACKAGE_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))
LOGGING_FILE = os.path.join('logs', '{}.log'.format(NAME_SHORT))
LANGUAGE_FILE_SUFFIX = '.yml'
DEFAULT_LANGUAGE = 'en_us'

PLUGIN_THREAD_POOL_SIZE = 4
MAX_TASK_QUEUE_SIZE = 2048
WAIT_TIME_AFTER_SERVER_STDOUT_END_SEC = 60
REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC = 5
