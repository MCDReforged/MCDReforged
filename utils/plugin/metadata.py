"""
Information of a plugin
"""
from utils import tool, constant
from utils.plugin.version import Version


class Metadata:
	def __init__(self, file_name, data):
		"""
		:param str file_name: file name of the plugin
		:param dict data: a dict with information of the plugin
		"""
		self.__data = data
		self.id = data.get('id', tool.remove_suffix(file_name, constant.PLUGIN_FILE_SUFFIX))
		self.version = Version(data.get('version', '0'), allow_wildcard=False)
		self.name = data.get('name', self.id)
		self.description = data.get('description', None)
		self.author = data.get('author', None)
		self.link = data.get('link', None)
		self.depends = data.get('dependencies', {})


__SAMPLE_METADATA = {
	'id': 'example-plugin',  # If missing it will be the file name without .py suffix
	'version': '1.0.0',  # If missing it will be '0'
	'name': 'Sample Plugin',  # RText is allowed
	'description': 'Sample plugin for MCDR',  # RText is allowed
	'author': 'Fallen_Breath',
	'link': 'https://github.com/Fallen-Breath/MCDReforged',
	'dependencies': {
		'MCDReforged': '>=0.10.0',
		'PlayerInfoAPI': '*'
	}
}
