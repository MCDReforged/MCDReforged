"""
Information of a plugin
"""
import re
from typing import List, Dict, TYPE_CHECKING, Optional, Union

from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.plugin.meta.version import Version, VersionParsingError, VersionRequirement
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_utils, class_utils
from mcdreforged.utils.types.message import TranslationLanguageDict

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class Metadata:
	"""
	The metadata of a MCDR plugin
	"""

	id: str
	"""
	The id of the plugin. Should match regexp ``[a-z][a-z0-9_]{0,63}``
	
	.. versionchanged:: v2.11.0
		
		Plugin id starts with non-alphabet character is no longer allowed
	"""

	version: Version
	"""The version of the plugin, in a less restrictive semver format"""

	name: str
	"""The name of the plugin"""

	description: Optional[Union[str, TranslationLanguageDict]]  # translation: lang -> description
	"""
	The description of the plugin
	
	It can be a regular str or a ``Dict[str, str]`` indicating a mapping from language to description
	"""

	author: Optional[List[str]]
	"""The authors of the plugin"""

	link: Optional[str]
	"""The url to the plugin, e.g. link to a github repository"""

	dependencies: Dict[str, VersionRequirement]
	"""
	A dict of dependencies the plugin relies on
	
	:Key: The id of the dependent plugin
	:Value: The version requirement of the dependent plugin
	"""

	entrypoint: str
	"""
	The entrypoint module of the plugin
	
	The entrypoint should be import-able
	"""

	archive_name: Optional[str]  # used in MCDR CLI only
	resources: Optional[List[str]]  # used in MCDR CLI only

	PLUGIN_ID_REGEX_OLD = re.compile(r'[a-z0-9_]{1,64}')
	PLUGIN_ID_REGEX = re.compile(r'[a-z][a-z0-9_]{0,63}')
	FALLBACK_VERSION = '0.0.0'

	def __init__(self, data: Optional[dict], *, plugin: Optional['AbstractPlugin'] = None):
		"""
		:param AbstractPlugin plugin: the plugin which this metadata is belonged to
		:param dict or None data: a dict with information of the plugin
		"""
		if not isinstance(data, dict):
			data = {}

		def warn(*args, **kwargs):
			if plugin is not None:
				plugin.mcdr_server.logger.warning(*args, **kwargs, stacklevel=3)

		plugin_name_text = repr(plugin)

		use_fallback_id_reason = None
		self.id = data.get('id')
		if self.id is None:
			use_fallback_id_reason = 'Plugin ID of {} not found'.format(plugin_name_text)
		else:
			bad_id = not isinstance(self.id, str)
			if self.PLUGIN_ID_REGEX.fullmatch(self.id) is None:
				bad_id = True
			if bad_id:
				use_fallback_id_reason = 'Plugin ID {!r} of {} is invalid'.format(self.id, plugin_name_text)
		if use_fallback_id_reason is not None:
			if plugin is not None:
				self.id = plugin.get_fallback_metadata_id()
				warn('{}, use fallback id {} instead'.format(use_fallback_id_reason, self.id))
			else:
				raise ValueError('Plugin id not found in metadata')
		class_utils.check_type(self.id, str)

		self.name = data.get('name', self.id)
		if isinstance(self.name, RTextBase):
			self.name = self.name.to_plain_text()
		class_utils.check_type(self.name, str)

		description = data.get('description')
		if isinstance(description, RTextBase):
			description = description.to_plain_text()
		self.description = description
		class_utils.check_type(self.description, [None, str, dict])

		self.author = data.get('author')
		if isinstance(self.author, str):
			self.author = [self.author]
		if isinstance(self.author, list):
			for i in range(len(self.author)):
				self.author[i] = str(self.author[i])
			if len(self.author) == 0:
				self.author = None
		class_utils.check_type(self.author, [None, list])

		self.link = data.get('link')
		class_utils.check_type(self.link, [None, str])

		version_str = data.get('version')
		if version_str:
			try:
				self.version = Version(version_str, allow_wildcard=False)
			except VersionParsingError as e:
				warn('Version {!r} of {} is invalid ({}), ignore and use fallback version instead {}'.format(version_str, plugin_name_text, e, self.FALLBACK_VERSION))
				version_str = None
		else:
			warn("{} doesn't specific a version, use fallback version {}".format(plugin_name_text, self.FALLBACK_VERSION))
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
		class_utils.check_type(self.entrypoint, str)
		# entrypoint module should be inside the plugin module
		if self.entrypoint != self.id and not self.entrypoint.startswith(self.id + '.'):
			raise ValueError('Invalid entry point {!r} for plugin id {!r}'.format(self.entrypoint, self.id))

		self.archive_name = data.get('archive_name')
		self.resources = data.get('resources', [])
		class_utils.check_type(self.archive_name, [None, str])
		class_utils.check_type(self.resources, list)

	def __repr__(self):
		return class_utils.represent(self)

	def get_description(self, lang: Optional[str] = None) -> Optional[str]:
		"""
		Return a translated plugin description in str

		:param lang: Optional, the language to translate to. When not specified it will use the language of MCDR
		:return: Translated plugin description
		"""
		if isinstance(self.description, str):
			return self.description
		if lang is None:
			lang = translation_utils.get_mcdr_language()
		return translation_utils.translate_from_dict(self.description, lang, default=None)

	def get_description_rtext(self) -> RTextBase:
		"""
		Return a translated plugin description in :class:`RText <mcdreforged.minecraft.rtext.text.RTextBase>`

		.. versionadded:: v2.1.2
		"""
		if isinstance(self.description, str):
			return RText(self.description)
		return RTextMCDRTranslation.from_translation_dict(self.description)

	def to_dict(self) -> dict:
		"""
		Create a dict present of this metadata object

		.. versionadded:: v2.13.0
		"""
		def copy(obj):
			return obj.copy() if isinstance(obj, (list, dict)) else obj

		return {
			# Fields for all plugins
			'id': self.id,
			'version': str(self.version),
			'name': self.name,
			'description': copy(self.description),
			'author': copy(self.author),
			'link': self.link,
			'dependencies': {k: str(v) for k, v in self.dependencies.items()},

			# Fields for packed plugins
			'entrypoint': self.entrypoint,
			'archive_name': self.archive_name,
			'resources': copy(self.resources),
		}


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
	'link': 'https://github.com/MCDReforged/MCDReforged',
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
Metadata(__SAMPLE_METADATA)  # there's should be no exception
