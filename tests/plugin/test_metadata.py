import io
import json
import warnings
from pathlib import Path
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
from pydantic import ValidationError

from mcdreforged.cli import cmd_pim
from mcdreforged.cli.cmd_pack import make_packed_plugin
from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.meta.metadata import Metadata, RequirementsFileSpec
from mcdreforged.plugin.meta.schema import Person, PluginMetadataJsonModel
from mcdreforged.plugin.type.multi_file_plugin import MultiFilePlugin
from mcdreforged.utils.exception import IllegalPluginStructure


def make_json_model(**kwargs) -> PluginMetadataJsonModel:
	return PluginMetadataJsonModel.model_validate({
		'id': 'test_plugin',
		'version': '1.2.3',
		**kwargs,
	}, strict=True)


def test_schema_version_is_only_used_during_parsing():
	model = make_json_model()
	assert model.schema_version == 0

	metadata = Metadata.create(model)
	assert not hasattr(metadata, 'schema_version')
	assert 'schema_version' not in metadata.to_dict()

	with warnings.catch_warnings(record=True) as records:
		warnings.simplefilter('always')
		Metadata.create(make_json_model(schema_version=plugin_constant.PLUGIN_METADATA_SCHEMA_VERSION))
	assert records == []

	future_model = make_json_model(schema_version=plugin_constant.PLUGIN_METADATA_SCHEMA_VERSION + 1)
	assert future_model.schema_version > plugin_constant.PLUGIN_METADATA_SCHEMA_VERSION


@pytest.mark.parametrize('authors', [
	'Alice',
	{'name': 'Alice', 'email': 'alice@example.com'},
	['Alice', {'name': 'Bob', 'homepage': 'https://example.com/bob'}],
])
def test_structured_person_fields_are_normalized_to_lists(authors):
	metadata = Metadata.create(make_json_model(authors=authors, maintainers=authors))
	assert isinstance(metadata.authors, list)
	assert isinstance(metadata.maintainers, list)
	assert len(metadata.authors) == (2 if isinstance(authors, list) else 1)
	assert len(metadata.maintainers) == len(metadata.authors)


def test_new_metadata_fields_survive_conversion():
	metadata = Metadata.create(make_json_model(
		authors={'name': 'Alice', 'email': 'alice@example.com'},
		maintainers=['Bob', {'name': 'Carol'}],
		links={
			'homepage': 'https://example.com',
			'source': 'https://example.com/source',
			'documentation': 'https://example.com/docs',
			'issues': 'https://example.com/issues',
		},
		license='LGPL-3.0-only',
		requirements_file='config/runtime-requirements.txt',
	))

	assert isinstance(metadata.authors[0], Person)
	assert metadata.license == 'LGPL-3.0-only'
	assert metadata.to_dict() == {
		'id': 'test_plugin',
		'version': '1.2.3',
		'name': 'test_plugin',
		'description': None,
		'authors': [{'name': 'Alice', 'email': 'alice@example.com', 'homepage': None}],
		'maintainers': [
			{'name': 'Bob', 'email': None, 'homepage': None},
			{'name': 'Carol', 'email': None, 'homepage': None},
		],
		'links': {
			'homepage': 'https://example.com',
			'source': 'https://example.com/source',
			'documentation': 'https://example.com/docs',
			'issues': 'https://example.com/issues',
		},
		'license': 'LGPL-3.0-only',
		'dependencies': {},
		'requirements_file': 'config/runtime-requirements.txt',
		'entrypoint': 'test_plugin',
		'archive_name': None,
		'resources': [],
	}


def test_unknown_fields_remain_ignored():
	model = PluginMetadataJsonModel.model_validate({
		'id': 'test_plugin',
		'version': '1.2.3',
		'unknown_field': {'anything': True},
	}, strict=True)
	assert 'unknown_field' not in model.model_dump()


def test_single_file_dict_remains_looser_than_json_model():
	metadata = Metadata.create({'id': 'test_plugin', 'version': '1.2.3', 'author': [123]})
	assert metadata.author == ['123']
	assert metadata.authors == [Person(name='123')]

	with pytest.raises(ValidationError):
		make_json_model(author=[123])
	with pytest.raises(TypeError, match='Invalid person item type int'):
		Metadata.create({'id': 'test_plugin', 'version': '1.2.3', 'authors': [123]})


def test_legacy_fields_are_marked_deprecated_by_pydantic():
	schema = PluginMetadataJsonModel.model_json_schema()
	assert schema['properties']['author']['deprecated'] is True
	assert schema['properties']['link']['deprecated'] is True

	model = make_json_model(author='Alice', link='https://example.com')
	with pytest.warns(DeprecationWarning):
		_ = model.author
	with pytest.warns(DeprecationWarning):
		_ = model.link


def test_legacy_fields_are_merged_into_canonical_runtime_fields():
	metadata = Metadata.create(make_json_model(
		author=['Legacy Alice', 'Legacy Bob'],
		authors=['New Carol', {'name': 'New Dave', 'email': 'dave@example.com'}],
		link='https://legacy.example.com',
		links={'source': 'https://example.com/source'},
	))

	assert [person.name for person in metadata.authors] == [
		'New Carol',
		'New Dave',
		'Legacy Alice',
		'Legacy Bob',
	]
	assert metadata.author == ['New Carol', 'New Dave', 'Legacy Alice', 'Legacy Bob']
	assert metadata.links.homepage == 'https://legacy.example.com'
	assert metadata.links.source == 'https://example.com/source'
	assert metadata.link == 'https://legacy.example.com'
	assert 'author' not in metadata.__dict__
	assert 'link' not in metadata.__dict__
	assert 'author' not in metadata.to_dict()
	assert 'link' not in metadata.to_dict()

	assert getattr(Metadata.author.fget, '__deprecated__', None) == 'Use authors instead'
	assert getattr(Metadata.link.fget, '__deprecated__', None) == 'Use links instead'


def test_new_link_homepage_wins_over_legacy_link():
	metadata = Metadata.create(make_json_model(
		link='https://legacy.example.com',
		links={
			'homepage': 'https://new.example.com',
			'source': 'https://example.com/source',
		},
	))
	assert metadata.links.homepage == 'https://new.example.com'
	assert metadata.link == 'https://new.example.com'


@pytest.mark.parametrize(('raw', 'mode', 'path', 'dict_value'), [
	({}, RequirementsFileSpec.Mode.AUTO, plugin_constant.PLUGIN_REQUIREMENTS_FILE, '<missing>'),
	({'requirements_file': None}, RequirementsFileSpec.Mode.DISABLED, None, None),
	({'requirements_file': 'requirements.txt'}, RequirementsFileSpec.Mode.REQUIRED, 'requirements.txt', 'requirements.txt'),
	({'requirements_file': 'deps/runtime.txt'}, RequirementsFileSpec.Mode.REQUIRED, 'deps/runtime.txt', 'deps/runtime.txt'),
])
def test_requirements_file_three_states_round_trip(raw, mode, path, dict_value):
	metadata = Metadata.create(make_json_model(**raw))
	assert metadata.requirements_file.mode is mode
	assert metadata.requirements_file.path == path

	dumped = metadata.to_dict()
	assert dumped.get('requirements_file', '<missing>') == dict_value
	assert Metadata.create(dumped).requirements_file == metadata.requirements_file


@pytest.mark.parametrize(('raw_path', 'normalized_path'), [
	('./deps//runtime.txt', 'deps/runtime.txt'),
	(r'deps\runtime.txt', 'deps/runtime.txt'),
])
def test_requirements_file_path_is_normalized(raw_path, normalized_path):
	metadata = Metadata.create(make_json_model(requirements_file=raw_path))
	assert metadata.requirements_file.path == normalized_path


@pytest.mark.parametrize('path', [
	'',
	'.',
	'..',
	'../requirements.txt',
	'deps/../requirements.txt',
	'/requirements.txt',
	r'\requirements.txt',
	r'C:\requirements.txt',
	r'C:requirements.txt',
	r'\\server\share\requirements.txt',
])
def test_requirements_file_path_must_stay_inside_plugin(path):
	with pytest.raises(ValueError, match='requirements_file must be'):
		Metadata.create(make_json_model(requirements_file=path))


class FakeMultiFilePlugin:
	def __init__(self, requirements_file: RequirementsFileSpec, content=None, open_error=None):
		self.metadata = SimpleNamespace(requirements_file=requirements_file)
		self.content = content
		self.open_error = open_error
		self.opened = []

	def get_metadata(self):
		return self.metadata

	def open_file(self, path):
		self.opened.append(path)
		if self.open_error is not None:
			raise self.open_error
		if self.content is None:
			raise FileNotFoundError(path)
		return io.BytesIO(self.content)


def check_requirements(plugin: FakeMultiFilePlugin):
	MultiFilePlugin._MultiFilePlugin__check_requirements(plugin)


def test_multi_file_plugin_requirements_file_modes():
	disabled = FakeMultiFilePlugin(RequirementsFileSpec.disabled())
	check_requirements(disabled)
	assert disabled.opened == []

	automatic = FakeMultiFilePlugin(RequirementsFileSpec.auto())
	check_requirements(automatic)
	assert automatic.opened == [plugin_constant.PLUGIN_REQUIREMENTS_FILE]

	required = FakeMultiFilePlugin(RequirementsFileSpec.required('deps/runtime.txt'))
	with pytest.raises(IllegalPluginStructure, match='deps/runtime.txt'):
		check_requirements(required)

	existing = FakeMultiFilePlugin(RequirementsFileSpec.required('deps/runtime.txt'), b'')
	check_requirements(existing)
	assert existing.opened == ['deps/runtime.txt']

	broken = FakeMultiFilePlugin(RequirementsFileSpec.auto(), open_error=PermissionError('denied'))
	with pytest.raises(PermissionError, match='denied'):
		check_requirements(broken)


def make_pack_source(tmp_path: Path, requirements_marker=...) -> Path:
	input_dir = tmp_path / 'input'
	(input_dir / 'test_plugin').mkdir(parents=True)
	(input_dir / 'test_plugin' / '__init__.py').write_text('', encoding='utf8')
	metadata = {'id': 'test_plugin', 'version': '1.2.3'}
	if requirements_marker is not ...:
		metadata['requirements_file'] = requirements_marker
	(input_dir / plugin_constant.PLUGIN_META_FILE).write_text(json.dumps(metadata), encoding='utf8')
	return input_dir


def pack(tmp_path: Path, input_dir: Path, *, ignore_patterns=None) -> Path:
	output_dir = tmp_path / 'output'
	make_packed_plugin(SimpleNamespace(
		input=str(input_dir),
		output=str(output_dir),
		name=None,
		ignore_patterns=ignore_patterns or [],
		ignore_file='',
		shebang='',
	), quiet=True)
	return output_dir / 'test_plugin-v1.2.3.mcdr'


def test_pack_preserves_custom_requirements_file_path(tmp_path):
	input_dir = make_pack_source(tmp_path, 'deps/runtime.txt')
	(input_dir / 'deps').mkdir()
	(input_dir / 'deps' / 'runtime.txt').write_text('example-package>=1\n', encoding='utf8')

	packed = pack(tmp_path, input_dir)
	with ZipFile(packed) as zip_file:
		assert 'deps/runtime.txt' in zip_file.namelist()
		assert 'runtime.txt' not in zip_file.namelist()


def test_pack_does_not_duplicate_requirements_inside_source(tmp_path):
	input_dir = make_pack_source(tmp_path, 'test_plugin/requirements.txt')
	(input_dir / 'test_plugin' / 'requirements.txt').write_text('example-package>=1\n', encoding='utf8')

	packed = pack(tmp_path, input_dir)
	with ZipFile(packed) as zip_file:
		assert zip_file.namelist().count('test_plugin/requirements.txt') == 1


def test_pack_rejects_required_requirements_excluded_by_ignore(tmp_path):
	input_dir = make_pack_source(tmp_path, 'deps/runtime.txt')
	(input_dir / 'deps').mkdir()
	(input_dir / 'deps' / 'runtime.txt').write_text('example-package>=1\n', encoding='utf8')

	packed = pack(tmp_path, input_dir, ignore_patterns=['deps/runtime.txt'])
	assert not packed.exists()


def test_pack_allows_automatic_requirements_excluded_by_ignore(tmp_path):
	input_dir = make_pack_source(tmp_path)
	(input_dir / plugin_constant.PLUGIN_REQUIREMENTS_FILE).write_text('example-package>=1\n', encoding='utf8')

	packed = pack(tmp_path, input_dir, ignore_patterns=[plugin_constant.PLUGIN_REQUIREMENTS_FILE])
	with ZipFile(packed) as zip_file:
		assert plugin_constant.PLUGIN_REQUIREMENTS_FILE not in zip_file.namelist()


def test_pack_requirements_file_auto_disabled_and_required(tmp_path):
	auto_dir = make_pack_source(tmp_path / 'auto')
	auto_packed = pack(tmp_path / 'auto', auto_dir)
	assert auto_packed.is_file()
	with ZipFile(auto_packed) as zip_file:
		assert plugin_constant.PLUGIN_REQUIREMENTS_FILE not in zip_file.namelist()

	disabled_dir = make_pack_source(tmp_path / 'disabled', None)
	(disabled_dir / plugin_constant.PLUGIN_REQUIREMENTS_FILE).write_text('ignored-package\n', encoding='utf8')
	disabled_packed = pack(tmp_path / 'disabled', disabled_dir)
	with ZipFile(disabled_packed) as zip_file:
		assert plugin_constant.PLUGIN_REQUIREMENTS_FILE not in zip_file.namelist()

	required_dir = make_pack_source(tmp_path / 'required', plugin_constant.PLUGIN_REQUIREMENTS_FILE)
	required_packed = pack(tmp_path / 'required', required_dir)
	assert not required_packed.exists()


def make_packed_plugin_file(path: Path, requirements_marker=..., requirements_content=None):
	metadata = {'id': 'test_plugin', 'version': '1.2.3'}
	if requirements_marker is not ...:
		metadata['requirements_file'] = requirements_marker
	with ZipFile(path, 'w') as zip_file:
		zip_file.writestr(plugin_constant.PLUGIN_META_FILE, json.dumps(metadata))
		if requirements_content is not None:
			file_name, content = requirements_content
			zip_file.writestr(file_name, content)


def test_pipi_reads_custom_requirements_file(tmp_path, monkeypatch):
	plugin_path = tmp_path / 'test.mcdr'
	make_packed_plugin_file(
		plugin_path,
		'deps/runtime.txt',
		('deps/runtime.txt', b'example-package>=1\nmcdreforged>=2\n'),
	)
	installed = []

	def fake_subprocess_call(command):
		if '-r' in command:
			installed.append(Path(command[command.index('-r') + 1]).read_bytes())
		return 0

	monkeypatch.setattr(cmd_pim.subprocess, 'call', fake_subprocess_call)
	assert cmd_pim.cmd_pipi([str(plugin_path)], quiet=True) is None
	assert installed == [b'example-package>=1']


def test_pipi_requirements_file_auto_disabled_and_required(tmp_path, monkeypatch):
	monkeypatch.setattr(cmd_pim.subprocess, 'call', lambda _: 0)

	automatic = tmp_path / 'automatic.mcdr'
	make_packed_plugin_file(automatic)
	assert cmd_pim.cmd_pipi([str(automatic)], quiet=True) is None

	disabled = tmp_path / 'disabled.mcdr'
	make_packed_plugin_file(
		disabled,
		None,
		(plugin_constant.PLUGIN_REQUIREMENTS_FILE, b'ignored-package\n'),
	)
	assert cmd_pim.cmd_pipi([str(disabled)], quiet=True) is None

	required = tmp_path / 'required.mcdr'
	make_packed_plugin_file(required, plugin_constant.PLUGIN_REQUIREMENTS_FILE)
	assert cmd_pim.cmd_pipi([str(required)], quiet=True) == 1
