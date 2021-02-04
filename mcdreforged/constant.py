"""
Constants for MCDR
"""

import os


NAME_SHORT = 'MCDR'
NAME = 'MCDReforged'
PACKAGE_NAME = 'mcdreforged'
VERSION = '1.3.0'       # semver
VERSION_PYPI = '1.3.0'  # pythonic ver
GITHUB_URL = 'https://github.com/Fallen-Breath/MCDReforged'
GITHUB_API_LATEST = 'https://api.github.com/repos/Fallen-Breath/MCDReforged/releases/latest'

LOGGING_FILE = os.path.join('logs', '{}.log'.format(NAME_SHORT))

PLUGIN_FILE_SUFFIX = '.py'
DISABLED_PLUGIN_FILE_SUFFIX = '.disabled'
LANGUAGE_FILE_SUFFIX = '.yml'

PLUGIN_THREAD_POOL_SIZE = 4
MAX_TASK_QUEUE_SIZE = 2048
WAIT_TIME_AFTER_SERVER_STDOUT_END_SEC = 60
REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC = 5
