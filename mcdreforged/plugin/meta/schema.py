import re
from typing import List, Dict, Optional, Union

from pydantic import BaseModel, Field, ConfigDict, StringConstraints
from typing_extensions import Annotated


class Person(BaseModel):
	name: str = Field(description='Name of the person')
	email: Optional[str] = Field(default=None, description='Email of the person')
	homepage: Optional[str] = Field(default=None, description='Homepage of the person')


class PluginLinks(BaseModel):
	homepage: Optional[str] = Field(default=None, description='Homepage of the plugin')
	source: Optional[str] = Field(default=None, description='Source repository of the plugin')
	documentation: Optional[str] = Field(default=None, description='Documentation page of the plugin')
	issue: Optional[str] = Field(default=None, description='Issue page of the plugin')


def __join_regex(segment: str, sep: str) -> re.Pattern:
	return re.compile(rf'^({segment})(({sep})({segment}))*$')


PluginId = Annotated[str, StringConstraints(
	pattern=re.compile(r'^[a-z][a-z0-9_]{0,63}$'),
)]
PluginVersion = Annotated[str, StringConstraints(
	pattern=re.compile(
		r'^\d+(\.\d+)*'
		r'(?:[-+][0-9A-Za-z]*(?:\.[0-9A-Za-z]+)*)*$'
	),
)]
PluginDescription = Union[
	None,
	Annotated[str, Field(description="The description of the plugin")],
	Annotated[
		Dict[
			Annotated[str, Field(description='The language code, e.g. en_us, zh_cn')],
			Annotated[str, Field(description='The description of the plugin in the given language')],
		],
		Field(description='The description translation mapping of the plugin. It maps from language to description string')
	],
]
PersonItem = Union[
	Annotated[str, Field(description='Name of the person')],
	Annotated[Person, Field(description="Detailed information of the person")],
]
PersonList = Union[None, PersonItem, List[PersonItem]]
PluginVersionRequirement = Annotated[str, StringConstraints(
	pattern=__join_regex(
		re.compile(
			r'(?:<=|>=|<|>|==|=|\^|~)?'
			r'[\dxX*]+(\.[\dxX*]+)*'
			r'(?:[-+][0-9A-Za-z]*(?:\.[0-9A-Za-z]+)*)*'
		).pattern,
		re.compile(r' ').pattern,
	))]
EntryPoint = Annotated[str, StringConstraints(pattern=__join_regex(
	re.compile(r'[a-z][a-z0-9_]{0,63}[a-zA-Z0-9_-]*').pattern,
	re.compile(r'\.').pattern,
))]


class PluginMetadataJsonModel(BaseModel):
	model_config = ConfigDict(
		json_schema_extra={
			'$id': f'https://json.schemastore.org/mcdreforged-plugin-metadata.json',
			'$schema': 'http://json-schema.org/draft-07/schema#'
		},
	)

	id: PluginId = Field(description='The identifier of the plugin')
	version: PluginVersion = Field(description='The version of the plugin, in a less restrictive semver format')
	name: Optional[str] = Field(default=None, description='The name of the plugin')
	description: PluginDescription = Field(default=None, description='The description of the plugin')

	author: Optional[Union[str, List[str]]] = Field(default=None, description='The author(s) of the plugin')
	# maintainer: PersonList = Field(default=None, description='The maintainer(s) of the plugin')
	link: Optional[str] = Field(default=None, description='The url to the plugin, e.g. link to a github repository')
	license: Optional[str] = Field(default=None, description='The license of the plugin. Recommended to use the SPDX License Identifiers')

	dependencies: Dict[PluginId, PluginVersionRequirement] = Field(default_factory=dict, description='A dict of dependencies the plugin relies on')
	# requirements_file: Optional[str] = Field(default='requirements.txt', description='Path to the Python package requirements file inside the multi-file plugin')
	entrypoint: Optional[EntryPoint] = Field(default=None, description='The entrypoint module of the multi-file plugin. The entrypoint should be import-able')

	# TODO: deprecate
	archive_name: Optional[str] = Field(default=None, description='The file name of generated .mcdr packed plugin in CLI')
	resources: Optional[List[str]] = Field(default=None, description='A list of file or folder names that will be packed into the generated .mcdr packed plugin file in CLI')


class PluginBuildConfigJsonModel(BaseModel):
	model_config = ConfigDict(
		extra='forbid',
		json_schema_extra={
			'$id': f'https://json.schemastore.org/mcdreforged-plugin-build-config.json',
			'$schema': 'http://json-schema.org/draft-07/schema#'
		},
	)

	archive_name: Optional[str] = Field(default=None, description='The file name of generated .mcdr packed plugin in CLI')
	resources: Optional[List[str]] = Field(default=None, description='A list of file or folder names that will be packed into the generated .mcdr packed plugin file in CLI')
	pack_ignorefile: str = Field(default='.gitignore', description='Path to the ignore file that will used during the CLI pack command')
