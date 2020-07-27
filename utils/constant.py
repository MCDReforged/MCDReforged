# -*- coding: utf-8 -*-

import os


VERSION = '0.9.4-alpha'
NAME_SHORT = 'MCDR'
NAME = 'MCDReforged'
NAME_FULL = 'MCDaemonReforged'
GITHUB_URL = 'https://github.com/Fallen-Breath/MCDReforged'
GITHUB_API_LATEST = 'https://api.github.com/repos/Fallen-Breath/MCDReforged/releases/latest'

CONFIG_FILE = 'config.yml'
PERMISSION_FILE = 'permission.yml'
LOGGING_FILE = os.path.join('log', '{}.log'.format(NAME_SHORT))
REACTOR_FOLDER = os.path.join('utils', 'reactor')
PARSER_FOLDER = os.path.join('utils', 'parser')
PLUGIN_FOLDER = 'plugins'
PLUGIN_CONFIG_FOLDER = 'config'
RESOURCE_FOLDER = 'resources'
LANGUAGE_FOLDER = os.path.join(RESOURCE_FOLDER, 'lang')
RE_DEATH_MESSAGE_FILE = os.path.join(RESOURCE_FOLDER, 'death_message.yml')
UPDATE_DOWNLOAD_FOLDER = 'MCDR_update'

REACTOR_FILE_SUFFIX = '.py'
PLUGIN_FILE_SUFFIX = '.py'
DISABLED_PLUGIN_FILE_SUFFIX = '.disabled'
LANGUAGE_FILE_SUFFIX = '.yml'

PLUGIN_THREAD_POOL_SIZE = 4
MAX_INFO_QUEUE_SIZE = 10000
WAIT_TIME_AFTER_SERVER_STDOUT_END_SEC = 60
REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC = 5
