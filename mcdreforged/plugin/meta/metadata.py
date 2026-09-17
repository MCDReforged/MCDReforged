"""
Information of a plugin
"""
import dataclasses
import enum
import re
from pathlib import PurePosixPath, PureWindowsPath
from typing import List, Dict, TYPE_CHECKING, Optional, Union, ClassVar, TypeVar, Any, cast, Type

from typing_extensions import deprecated, override

from mcdreforged.constants import plugin_constant
from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel, Person, PluginLinks
from mcdreforged.plugin.meta.version import Version, VersionParsingError, VersionRequirement
from mcdreforged.translation.translation_text import RTextMCDRTranslation
from mcdreforged.utils import translation_utils, class_utils
from mcdreforged.utils.types.message import TranslationLanguageDict

if TYPE_CHECKING:
	from mcdreforged.plugin.type.plugin import AbstractPlugin

_T = TypeVar('_T')


def _none_or(value: Optional[_T], default: _T) -> _T:
	return value if value is not None else default


def _normalize_requirements_file_path(path: str) -> str:
	windows_path = PureWindowsPath(path)
	posix_path = PurePosixPath(path.replace('\\', '/'))
	if (
		'\0' in path or
		windows_path.drive or
		windows_path.root or
		posix_path.is_absolute() or
		'..' in posix_path.parts
	):
		raise ValueError('requirements_file must be a relative path inside the plugin, found {!r}'.format(path))
	normalized = posix_path.as_posix()
	if normalized in ('', '.'):
		raise ValueError('requirements_file must be a non-empty file path, found {!r}'.format(path))
	return normalized


@dataclasses.dataclass(frozen=True)
class RequirementsFileSpec:
	"""The declared handling strategy for a multi-file plugin's Python requirements file."""

	class Mode(enum.Enum):
		AUTO = 'auto'
		DISABLED = 'disabled'
		REQUIRED = 'required'

	mode: Mode
	path: Optional[str]

	def __post_init__(self):
		if not isinstance(self.mode, self.Mode):
			raise TypeError('mode should be RequirementsFileSpec.Mode, found {}'.format(type(self.mode).__name__))
		if self.mode is self.Mode.AUTO and self.path != plugin_constant.PLUGIN_REQUIREMENTS_FILE:
			raise ValueError('path should be {!r} in auto mode, found {!r}'.format(plugin_constant.PLUGIN_REQUIREMENTS_FILE, self.path))
		if self.mode is self.Mode.DISABLED and self.path is not None:
			raise ValueError('path should be None in disabled mode, found {!r}'.format(self.path))
		if self.mode is self.Mode.REQUIRED:
			if not isinstance(self.path, str):
				raise TypeError('path should be str in required mode, found {}'.format(type(self.path).__name__))
			object.__setattr__(self, 'path', _normalize_requirements_file_path(self.path))

	@classmethod
	def auto(cls) -> 'RequirementsFileSpec':
		return cls(cls.Mode.AUTO, plugin_constant.PLUGIN_REQUIREMENTS_FILE)

	@classmethod
	def disabled(cls) -> 'RequirementsFileSpec':
		return cls(cls.Mode.DISABLED, None)

	@classmethod
	def required(cls, path: str) -> 'RequirementsFileSpec':
		return cls(cls.Mode.REQUIRED, path)

	@classmethod
	def from_declaration(cls, value: Optional[str], *, declared: bool) -> 'RequirementsFileSpec':
		if not declared:
			return cls.auto()
		if value is None:
			return cls.disabled()
		return cls.required(value)

	@classmethod
	def from_model(cls, model: PluginMetadataJsonModel) -> 'RequirementsFileSpec':
		return cls.from_declaration(
			model.requirements_file,
			declared='requirements_file' in model.model_fields_set,
		)


def _normalize_person_list(value: Any) -> List[Person]:
	if value is None:
		return []
	if not isinstance(value, list):
		value = [value]

	result: List[Person] = []
	for item in value:
		if isinstance(item, str):
			person = Person(name=item)
		elif isinstance(item, Person):
			person = item
		elif isinstance(item, dict):
			person = Person.model_validate(item)
		else:
			raise TypeError('Invalid person item type {}, expected str, dict, or Person'.format(type(item).__name__))
		result.append(person)
	return result


def _normalize_legacy_authors(value: Any) -> List[Person]:
	if value is None:
		return []
	if isinstance(value, str):
		names = [value]
	else:
		names = class_utils.check_type(value, list)
	return [Person(name=str(name)) for name in names]


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

	authors: Optional[List[Person]]
	"""The authors of the plugin"""

	maintainers: Optional[List[Person]]
	"""The maintainers of the plugin"""

	links: Optional[PluginLinks]
	"""The links related to the plugin"""

	license: Optional[str]
	"""The license of the plugin"""

	dependencies: Dict[str, VersionRequirement]
	"""
	A dict of dependencies the plugin relies on
	
	:Key: The id of the dependent plugin
	:Value: The version requirement of the dependent plugin
	"""

	requirements_file: RequirementsFileSpec
	"""The defination of the Python requirements file inside the multi-file plugin"""

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

		if isinstance(data, PluginMetadataJsonModel):
			legacy_fields = data.model_dump(include={'author', 'link'})
			legacy_authors = legacy_fields['author']
			legacy_link = legacy_fields['link']
		else:
			legacy_authors = data.get('author')
			legacy_link = data.get('link')

		def create_maintainers() -> Optional[List[Person]]:
			if isinstance(data, PluginMetadataJsonModel):
				value = data.maintainers
			else:
				value = data.get('maintainers')
			result = _normalize_person_list(value)
			return result or None

		def create_authors() -> Optional[List[Person]]:
			if isinstance(data, PluginMetadataJsonModel):
				new_authors = data.authors
			else:
				new_authors = data.get('authors')
			result = _normalize_person_list(new_authors)
			result.extend(_normalize_legacy_authors(legacy_authors))
			return result or None

		def create_links() -> Optional[PluginLinks]:
			if isinstance(data, PluginMetadataJsonModel):
				meta_links = data.links
			else:
				meta_links = data.get('links')
			if isinstance(meta_links, dict):
				meta_links = PluginLinks.model_validate(meta_links)
			meta_links = class_utils.check_type(meta_links, (None, PluginLinks))
			checked_legacy_link = class_utils.check_type(legacy_link, (None, str))
			if checked_legacy_link is not None and (meta_links is None or meta_links.homepage is None):
				if meta_links is None:
					meta_links = PluginLinks(homepage=checked_legacy_link)
				else:
					meta_links = meta_links.model_copy(update={'homepage': checked_legacy_link})
			return meta_links

		def create_license() -> Optional[str]:
			if isinstance(data, PluginMetadataJsonModel):
				return data.license
			return class_utils.check_type(data.get('license'), (None, str))

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

		if isinstance(data, PluginMetadataJsonModel):
			requirements_file = RequirementsFileSpec.from_model(data)
		else:
			requirements_file = RequirementsFileSpec.from_declaration(
				class_utils.check_type(data.get('requirements_file'), (None, str)),
				declared='requirements_file' in data,
			)

		return cls(
			id=meta_id,
			version=create_version(),
			name=create_name(),
			description=create_description(),
			authors=create_authors(),
			maintainers=create_maintainers(),
			links=create_links(),
			license=create_license(),
			dependencies=create_dependencies(),
			requirements_file=requirements_file,
			entrypoint=create_entrypoint(),
			archive_name=create_archive_name(),
			resources=create_resources(),
		)

	@property
	@deprecated('Use authors instead', category=None)
	def author(self) -> Optional[List[str]]:
		"""
		The author names of the plugin

		.. deprecated:: v2.16.0
			Use :attr:`authors` instead.
		"""
		if self.authors is None:
			return None
		return [person.name for person in self.authors]

	@property
	@deprecated('Use links instead', category=None)
	def link(self) -> Optional[str]:
		"""
		The homepage of the plugin

		.. deprecated:: v2.16.0
			Use :attr:`links` instead.
		"""
		if self.links is None:
			return None
		return self.links.homepage

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

		def person_list_to_json(items: Optional[List[Person]]):
			if items is None:
				return None
			return [item.model_dump(mode='json') for item in items]

		result = {
			# Fields for all plugins
			'id': self.id,
			'version': str(self.version),
			'name': self.name,
			'description': copy(self.description),
			'authors': person_list_to_json(self.authors),
			'maintainers': person_list_to_json(self.maintainers),
			'links': self.links.model_dump(mode='json') if self.links is not None else None,
			'license': self.license,
			'dependencies': {k: str(v) for k, v in self.dependencies.items()},

			# Fields for packed plugins
			'entrypoint': self.entrypoint,
			'archive_name': self.archive_name,
			'resources': copy(self.resources),
		}
		if self.requirements_file.mode is RequirementsFileSpec.Mode.DISABLED:
			result['requirements_file'] = None
		elif self.requirements_file.mode is RequirementsFileSpec.Mode.REQUIRED:
			result['requirements_file'] = self.requirements_file.path
		return result


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
