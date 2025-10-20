"""
Information of a plugin
"""
import dataclasses
import re
from typing import List, Dict, TYPE_CHECKING, Optional, Union, ClassVar, TypeVar, Any, cast, Type

from typing_extensions import override

from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel
from mcdreforged.plugin.meta.version import Version, VersionParsingError, VersionRequirement
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_utils, class_utils
from mcdreforged.utils.types.message import TranslationLanguageDict

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin

_T = TypeVar('_T')


def _none_or(value: Optional[_T], default: _T) -> _T:
	return value if value is not None else default


class __MetadataMeta(type):
	@override
	def __call__(cls: type[_T], *args: Any, **kwargs: Any) -> _T:
		if cls is Metadata and len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], dict):
			# compat old usage (before v2.16.0) that pass a single dict into the constructor
			# XXX: drop this compactibility hack in v3?
			return cast(_T, cast(Type[Metadata], cls).create(args[0]))
		else:
			return type.__call__(cls, *args, **kwargs)


@dataclasses.dataclass(frozen=True)
class Metadata(metaclass=__MetadataMeta):
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

	PLUGIN_ID_REGEX_OLD: ClassVar[re.Pattern] = re.compile(r'[a-z0-9_]{1,64}')
	PLUGIN_ID_REGEX: ClassVar[re.Pattern] = re.compile(r'[a-z][a-z0-9_]{0,63}')
	FALLBACK_VERSION: ClassVar[str] = '0.0.0'

	@classmethod
	def create(cls, data: Union[dict, PluginMetadataJsonModel], *, plugin: Optional['AbstractPlugin'] = None) -> 'Metadata':
		"""
		:param AbstractPlugin plugin: the plugin which this metadata is belonged to
		:param dict or None data: a dict with information of the plugin

		.. versionadded:: v2.16.0
		"""
		class_utils.check_type(data, (dict, PluginMetadataJsonModel))
		plugin_name_text = repr(plugin)

		def warn(*args, **kwargs):
			if plugin is not None:
				plugin.mcdr_server.logger.warning(*args, **kwargs, stacklevel=3)

		def create_id() -> str:
			if isinstance(data, PluginMetadataJsonModel):
				return data.id
			if (plugin_id := data.get('id')) is not None:
				if isinstance(plugin_id, str) and cls.PLUGIN_ID_REGEX.fullmatch(plugin_id):
					return plugin_id
				use_fallback_id_reason = 'Plugin ID {!r} of {} is invalid'.format(plugin_id, plugin_name_text)
			else:
				use_fallback_id_reason = 'Plugin ID of {} not found'.format(plugin_name_text)

			if plugin is not None:
				fallback_id = plugin.get_fallback_metadata_id()
				warn('{}, use fallback id {} instead'.format(use_fallback_id_reason, fallback_id))
				return fallback_id
			else:
				raise ValueError('Plugin id not found in metadata')

		meta_id = create_id()

		def create_name() -> str:
			if isinstance(data, PluginMetadataJsonModel):
				return _none_or(data.name, meta_id)
			meta_name = data.get('name', meta_id)
			if isinstance(meta_name, RTextBase):
				meta_name = meta_name.to_plain_text()
			class_utils.check_type(meta_name, str)
			return meta_name

		def create_description() -> Optional[Union[str, TranslationLanguageDict]]:
			if isinstance(data, PluginMetadataJsonModel):
				return data.description
			description = data.get('description')
			if isinstance(description, RTextBase):
				description = description.to_plain_text()
			meta_description = description
			class_utils.check_type(meta_description, (None, str, dict))
			return meta_description

		def create_author() -> Optional[List[str]]:
			if isinstance(data, PluginMetadataJsonModel):
				return [data.author] if isinstance(data.author, str) else data.author
			meta_author = data.get('author')
			if isinstance(meta_author, str):
				meta_author = [meta_author]
			if isinstance(meta_author, list):
				for i in range(len(meta_author)):
					meta_author[i] = str(meta_author[i])
				if len(meta_author) == 0:
					meta_author = None
			class_utils.check_type(meta_author, (None, list))
			return meta_author

		def create_link() -> Optional[str]:
			if isinstance(data, PluginMetadataJsonModel):
				return data.link
			meta_link = data.get('link')
			class_utils.check_type(meta_link, (None, str))
			return meta_link

		def create_version() -> Version:
			if (version_str := data.version if isinstance(data, PluginMetadataJsonModel) else data.get('version')) is not None:
				try:
					return Version(version_str, allow_wildcard=False)
				except VersionParsingError as e:
					warn('Version {!r} of {} is invalid ({}), ignore and use fallback version instead {}'.format(version_str, plugin_name_text, e, cls.FALLBACK_VERSION))
			else:
				warn("{} doesn't specific a version, use fallback version {}".format(plugin_name_text, cls.FALLBACK_VERSION))
			return Version(cls.FALLBACK_VERSION)

		def create_dependencies() -> Dict[str, VersionRequirement]:
			meta_dependencies = {}
			raw_dependencies: Dict[str, str] = data.dependencies if isinstance(data, PluginMetadataJsonModel) else data.get('dependencies', {})
			for plugin_id, requirement in raw_dependencies.items():
				try:
					meta_dependencies[plugin_id] = VersionRequirement(requirement)
				except VersionParsingError as e:
					warn('Dependency "{}: {}" of {} is invalid ({}), ignore'.format(
						plugin_id, requirement, plugin_name_text, e
					))
			return meta_dependencies

		def create_entrypoint() -> str:
			if isinstance(data, PluginMetadataJsonModel):
				meta_entrypoint = _none_or(data.entrypoint, meta_id)
			else:
				meta_entrypoint = data.get('entrypoint', meta_id)
			class_utils.check_type(meta_entrypoint, str)
			# entrypoint module should be inside the plugin module
			if meta_entrypoint != meta_id and not meta_entrypoint.startswith(meta_id + '.'):
				raise ValueError('Invalid entry point {!r} for plugin id {!r}'.format(meta_entrypoint, meta_id))
			return meta_entrypoint

		def create_archive_name() -> Optional[str]:
			if isinstance(data, PluginMetadataJsonModel):
				return data.archive_name
			else:
				return class_utils.check_type(data.get('archive_name'), (None, str))

		def create_resources() -> List[str]:
			if isinstance(data, PluginMetadataJsonModel):
				return _none_or(data.resources, [])
			else:
				return class_utils.check_type(data.get('resources', []), list)

		return cls(
			id=meta_id,
			version=create_version(),
			name=create_name(),
			description=create_description(),
			author=create_author(),
			link=create_link(),
			dependencies=create_dependencies(),
			entrypoint=create_entrypoint(),
			archive_name=create_archive_name(),
			resources=create_resources(),
		)

	def get_description(self, lang: Optional[str] = None) -> Optional[str]:
		"""
		Return a translated plugin description in str

		:param lang: Optional, the language to translate to. When not specified it will use the language of MCDR
		:return: Translated plugin description
		"""
		if self.description is None:
			return None
		if isinstance(self.description, str):
			return self.description
		if lang is None:
			lang = translation_utils.get_mcdr_language()
		result = translation_utils.translate_from_dict(self.description, lang, default=None)
		return class_utils.check_type(result, (str, None))

	def get_description_rtext(self) -> RTextBase:
		"""
		Return a translated plugin description in :class:`RText <mcdreforged.minecraft.rtext.text.RTextBase>`

		.. versionadded:: v2.1.2
		"""
		if self.description is None:
			raise ValueError('description is None')
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


def __sample_test():
	sample_metadata = {
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

	# there's should be no exception on both new method and old method
	meta1 = Metadata.create(sample_metadata)
	meta2 = Metadata(sample_metadata)  # type: ignore
	if meta1 != meta2:
		raise AssertionError(f'{meta1} != {meta2}')

__sample_test()

