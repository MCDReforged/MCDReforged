"""
Constants related to plugin for MCDR
"""

# the directory inside MCDR working directory that stores plugins' configure files
PLUGIN_CONFIG_DIRECTORY = 'config'

# The file prefix for a solo plugin (a single .py file)
SOLO_PLUGIN_FILE_SUFFIX = '.py'

# The file prefix for a packed plugin (a zipped file)
PACKED_PLUGIN_FILE_SUFFIXES = ('.mcdr', '.pyz')

# The name of the meta file inside a packed plugin
PLUGIN_META_FILE = 'mcdreforged.plugin.json'

# The name of the python package requirement file
PLUGIN_REQUIREMENTS_FILE = 'requirements.txt'

# the path to the directory inside a packed plugin as the default directory to store the language files of the plugin
PLUGIN_TRANSLATION_FILES_PATH = 'lang'

# Disabled plugin file name suffix
DISABLED_PLUGIN_FILE_SUFFIX = '.disabled'
