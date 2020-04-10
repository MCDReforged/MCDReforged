# -*- coding: utf-8 -*-

import os


VERSION = '0.7.0-alpha'
NAME_SHORT = 'MCDR'
NAME = 'MCDReforged'
NAME_FULL = 'MCDaemonReforged'

CONFIG_FILE = 'config.yml'
PERMISSION_FILE = 'permission.yml'
LOGGING_FILE = 'log/{}.log'.format(NAME_SHORT)
REACTOR_FOLDER = 'utils/reactor/'
PARSER_FOLDER = 'utils/parser/'
PLUGIN_FOLDER = 'plugins/'
RESOURCE_FOLDER = 'resources/'
LANGUAGE_FOLDER = os.path.join(RESOURCE_FOLDER, 'lang/')
RE_DEATH_MESSAGE_FILE = os.path.join(RESOURCE_FOLDER, 'death_message.yml')
UPDATE_DOWNLOAD_FOLDER = 'MCDR_update/'
