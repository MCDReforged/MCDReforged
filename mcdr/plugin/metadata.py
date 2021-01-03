"""
Information of a plugin
"""
from typing import List, Dict

from mcdr import constant
from mcdr.plugin.version import Version, VersionParsingError, VersionRequirement
from mcdr.rtext import RTextBase
from mcdr.utils import string_util


class MetaData:
	id: str
	version: Version
	name: str or RTextBase
	description: str or RTextBase or None
	author: str or List[str] or None
	link: str or None
	dependencies: Dict[str, VersionRequirement]

	FALLBACK_VERSION = '0.0.0'

	def __init__(self, plugin, data):
		"""
		:param Plugin plugin: the plugin which this metadata is belong to
		:param dict or None data: a dict with information of the plugin
		"""
		if not isinstance(data, dict):
			data = {}
		fallback_id = string_util.remove_suffix(plugin.file_name, constant.PLUGIN_FILE_SUFFIX)
		logger = plugin.mcdr_server.logger

		self.id = data.get('id', fallback_id)
		self.name = data.get('name', self.id)
		self.description = data.get('description', None)
		self.author = data.get('author', None)
		self.link = data.get('link', None)

		version_str = data.get('version')
		if version_str:
			try:
				self.version = Version(version_str, allow_wildcard=False)
			except VersionParsingError as e:
				logger.warning('Version "{}" of {} is invalid ({}), ignore and use fallback version instead {}'.format(
					version_str, plugin.get_name(), e, self.FALLBACK_VERSION
				))
				version_str = None
		else:
			logger.warning('{} doesn\'t specific a version, use fallback version {}'.format(plugin.get_name(), self.FALLBACK_VERSION))
		if version_str is None:
			self.version = Version(self.FALLBACK_VERSION)

		self.dependencies = {}
		for plugin_id, requirement in data.get('dependencies', {}).items():
			try:
				self.dependencies[plugin_id] = VersionRequirement(requirement)
			except VersionParsingError as e:
				logger.warning('Dependency "{}: {}" of {} is invalid ({}), ignore'.format(
					plugin_id, requirement, plugin.get_name(), e
				))


__SAMPLE_METADATA = {
	'id': 'example-plugin',  # If missing it will be the file name without .py suffix
	'version': '1.0.0',  # If missing it will be '0.0.0'
	'name': 'Sample Plugin',  # RText is allowed
	'description': 'Sample plugin for MCDR',  # RText is allowed
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/Fallen-Breath/MCDReforged',
	'dependencies': {
		'MCDReforged': '>=1.0.0',
		'PlayerInfoAPI': '*'
	}
}
