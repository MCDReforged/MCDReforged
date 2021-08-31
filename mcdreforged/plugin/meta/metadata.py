"""
Information of a plugin
"""
import re
from typing import List, Dict, TYPE_CHECKING, Optional, Union

from mcdreforged.minecraft.rtext import RTextBase, RText
from mcdreforged.plugin.meta.version import Version, VersionParsingError, VersionRequirement
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_util, misc_util
from mcdreforged.utils.types import TranslationLanguageDict

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class Metadata:
	id: str
	version: Version
	name: str
	description: Optional[Union[str, TranslationLanguageDict]]  # translation: lang -> description
	author: Optional[List[str]]
	link: Optional[str]
	dependencies: Dict[str, VersionRequirement]

	entrypoint: str
	archive_name: Optional[str]
	resources: Optional[List[str]]

	FALLBACK_VERSION = '0.0.0'

	def __init__(self, data: Optional[dict], *, plugin: Optional['AbstractPlugin'] = None):
		"""
		:param AbstractPlugin plugin: the plugin which this metadata is belong to
		:param dict or None data: a dict with information of the plugin
		"""
		if not isinstance(data, dict):
			data = {}

		def warn(*args, **kwargs):
			if plugin is not None:
				plugin.mcdr_server.logger.warning(*args, **kwargs)

		plugin_name_text = repr(plugin)

		use_fallback_id_reason = None
		self.id = data.get('id')
		if self.id is None:
			use_fallback_id_reason = 'Plugin ID of {} not found'.format(plugin_name_text)
		elif not isinstance(self.id, str) or re.fullmatch(r'[a-z0-9_]{1,64}', self.id) is None:
			use_fallback_id_reason = 'Plugin ID "{}" of {} is invalid'.format(self.id, plugin_name_text)
		if use_fallback_id_reason is not None:
			if plugin is not None:
				self.id = plugin.get_fallback_metadata_id()
				warn('{}, use fallback id {} instead'.format(use_fallback_id_reason, self.id))
			else:
				raise ValueError('Plugin id not found in metadata')
		misc_util.check_type(self.id, str)

		self.name = data.get('name', self.id)
		if isinstance(self.name, RTextBase):
			self.name = self.name.to_plain_text()
		misc_util.check_type(self.name, str)

		description = data.get('description')
		if isinstance(description, RTextBase):
			description = description.to_plain_text()
		self.description = description
		misc_util.check_type(self.description, [type(None), str, dict])

		self.author = data.get('author')
		if isinstance(self.author, str):
			self.author = [self.author]
		if isinstance(self.author, list):
			for i in range(len(self.author)):
				self.author[i] = str(self.author[i])
			if len(self.author) == 0:
				self.author = None
		misc_util.check_type(self.author, [type(None), list])

		self.link = data.get('link')
		misc_util.check_type(self.link, [type(None), str])

		version_str = data.get('version')
		if version_str:
			try:
				self.version = Version(version_str, allow_wildcard=False)
			except VersionParsingError as e:
				warn('Version "{}" of {} is invalid ({}), ignore and use fallback version instead {}'.format(version_str, plugin_name_text, e, self.FALLBACK_VERSION))
				version_str = None
		else:
			warn('{} doesn\'t specific a version, use fallback version {}'.format(plugin_name_text, self.FALLBACK_VERSION))
		if version_str is None:
			self.version = Version(self.FALLBACK_VERSION)

		self.dependencies = {}
		for plugin_id, requirement in data.get('dependencies', {}).items():
			try:
				self.dependencies[plugin_id] = VersionRequirement(requirement)
			except VersionParsingError as e:
				warn('Dependency "{}: {}" of {} is invalid ({}), ignore'.format(
					plugin_id, requirement, plugin_name_text, e
				))

		self.entrypoint = data.get('entrypoint', self.id)
		misc_util.check_type(self.entrypoint, str)
		# entrypoint module should be inside the plugin module
		if self.entrypoint != self.id and not self.entrypoint.startswith(self.id + '.'):
			raise ValueError('Invalid entry point "{}" for plugin id "{}"'.format(self.entrypoint, self.id))

		self.archive_name = data.get('archive_name')
		self.resources = data.get('resources', [])
		misc_util.check_type(self.archive_name, [type(None), str])
		misc_util.check_type(self.resources, list)

	def __repr__(self):
		return misc_util.represent(self)

	def get_description(self, lang: Optional[str] = None) -> Optional[str]:
		"""
		Get translated description str
		"""
		if isinstance(self.description, str):
			return self.description
		return translation_util.translate_from_dict(self.description, lang, default=None)

	def get_description_rtext(self) -> RTextBase:
		if isinstance(self.description, str):
			return RText(self.description)
		return RTextMCDRTranslation.from_translation_dict(self.description)


__SAMPLE_METADATA = {
	'id': 'example_plugin',   # If missing it will be the file name without .py suffix
	'version': '1.0.0',       # If missing it will be '0.0.0'
	'name': 'Sample Plugin',
	# single string description is also supported
	# 'description': 'Sample plugin for MCDR',
	'description': {
		'en_us': 'Sample plugin for MCDR'
	},
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/Fallen-Breath/MCDReforged',
	'dependencies': {
		'mcdreforged': '>=1.0.0'
	},

	# Fields for packed plugins
	'entrypoint': 'example_plugin.entry',
	'archive_name': 'MyExamplePlugin-v{version}',
	'resources': [
		'my_resource_folder',
		'another_resource_file',
	]
}
