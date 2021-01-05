"""
Information of a plugin
"""
from typing import List, Dict, TYPE_CHECKING

from mcdreforged.plugin.version import Version, VersionParsingError, VersionRequirement
from mcdreforged.rtext import RTextBase

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin import AbstractPlugin


class MetaData:
	id: str
	version: Version
	name: RTextBase
	description: RTextBase or None
	author: List[str] or None
	link: str or None
	dependencies: Dict[str, VersionRequirement]

	FALLBACK_VERSION = '0.0.0'

	def __init__(self, plugin: 'AbstractPlugin', data: dict):
		"""
		:param AbstractPlugin plugin: the plugin which this metadata is belong to
		:param dict or None data: a dict with information of the plugin
		"""
		if not isinstance(data, dict):
			data = {}
		logger = plugin.mcdr_server.logger

		self.id = data.get('id', plugin.get_fallback_metadata_id())

		self.name = RTextBase.from_any(data.get('name', self.id))

		self.description = data.get('description', None)
		if self.description is not None:
			self.description = RTextBase.from_any(self.description)

		self.author = data.get('author', None)
		if isinstance(self.author, str):
			self.author = [self.author]
		if isinstance(self.author, list):
			for i in range(len(self.author)):
				self.author[i] = str(self.author[i])
			if len(self.author) == 0:
				self.author = None

		self.link = data.get('link', None)
		if not isinstance(self.link, str):
			self.link = None

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
