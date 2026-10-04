import dataclasses
import re
import tempfile
import urllib.parse
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from zipfile import ZipFile

from mcdreforged.constants import plugin_constant
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.abort_helper import AbortHelper
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.uri_plugin_specifier import UriPluginSpecifier, UriScheme
from mcdreforged.plugin.installer.downloader import DirectDownloader
from mcdreforged.plugin.meta.metadata import Metadata, RequirementsFileSpec
from mcdreforged.plugin.meta.schema import PluginMetadataJsonModel
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils import file_utils


@dataclasses.dataclass(frozen=True)
class PreparedUriPlugin:
	specifier: UriPluginSpecifier
	local_path: Path
	metadata: Metadata
	requirements: List[str]
	file_name: str
	file_size: int
	file_sha256: str


class UriPluginPrepareHelper:
	class Aborted(Exception):
		pass

	__MAX_PLUGIN_SIZE = 100 * 1024 * 1024
	__MAX_METADATA_SIZE = 100 * 1024

	def __init__(self, data_dir: Path, download_timeout: float, abort_helper: AbortHelper):
		self.__data_dir = data_dir
		self.__download_timeout = download_timeout
		self.__abort_helper = abort_helper
		self.__temp_directory: Optional[tempfile.TemporaryDirectory] = None
		self.__next_file_id = 0

	def __enter__(self) -> 'UriPluginPrepareHelper':
		self.__check_abort()
		self.__data_dir.mkdir(parents=True, exist_ok=True)
		self.__temp_directory = tempfile.TemporaryDirectory(prefix='pim_uri_', dir=self.__data_dir)
		return self

	def __exit__(self, exc_type, exc_value, traceback):
		if self.__temp_directory is not None:
			self.__temp_directory.cleanup()
			self.__temp_directory = None

	def prepare(self, specifier: UriPluginSpecifier) -> PreparedUriPlugin:
		self.__check_abort()
		if self.__temp_directory is None:
			raise RuntimeError('URI preparation requires an active context manager')
		target = Path(self.__temp_directory.name) / '{}.tmp'.format(self.__next_file_id)
		self.__next_file_id += 1
		if specifier.scheme is UriScheme.file:
			assert isinstance(specifier.location, Path)
			self.__copy_file(specifier.location, target)
			names = [specifier.location.name]
		else:
			assert isinstance(specifier.location, urllib.parse.SplitResult)
			downloader = DirectDownloader(
				specifier.uri, target, self.__download_timeout, max_size=self.__MAX_PLUGIN_SIZE,
			)
			try:
				with self.__abort_helper.with_abort_callback(downloader.abort):
					self.__check_abort()
					result = downloader.download()
			except DirectDownloader.Aborted:
				raise self.Aborted() from None
			names = list(result.suggested_file_names)
			names.extend(
				urllib.parse.unquote(urllib.parse.urlsplit(url).path.rsplit('/', 1)[-1])
				for url in (result.final_url, specifier.uri)
			)

		self.__check_abort()
		file_hash = file_utils.calc_file_sha256(target)
		if specifier.expected_sha256 is not None and not file_hash.startswith(specifier.expected_sha256):
			raise ValueError('SHA256 mismatched, expected {}, actual {}'.format(specifier.expected_sha256, file_hash))
		self.__check_abort()
		metadata, requirements = self.__read_metadata(target)
		self.__check_abort()
		return PreparedUriPlugin(
			specifier=specifier,
			local_path=target,
			metadata=metadata,
			requirements=requirements,
			file_name=self.__choose_file_name(names, metadata),
			file_size=target.stat().st_size,
			file_sha256=file_hash,
		)

	def __check_abort(self):
		if self.__abort_helper.is_aborted():
			raise self.Aborted()

	def __copy_file(self, source: Path, target: Path):
		if not source.is_file():
			raise ValueError('Plugin file {!s} is not a regular file'.format(source))
		if source.stat().st_size > self.__MAX_PLUGIN_SIZE:
			raise ValueError('Plugin file exceeds the 100 MiB limit')
		size = 0
		with source.open('rb') as src, target.open('xb') as dst:
			while chunk := src.read(8192):
				self.__check_abort()
				size += len(chunk)
				if size > self.__MAX_PLUGIN_SIZE:
					raise ValueError('Plugin file exceeds the 100 MiB limit')
				dst.write(chunk)

	def __read_archive_member(self, archive: ZipFile, name: str) -> bytes:
		if archive.getinfo(name).file_size > self.__MAX_METADATA_SIZE:
			raise ValueError('{} exceeds the 100 KiB limit'.format(name))
		with archive.open(name) as f:
			data = f.read(self.__MAX_METADATA_SIZE + 1)
		if len(data) > self.__MAX_METADATA_SIZE:
			raise ValueError('{} exceeds the 100 KiB limit'.format(name))
		return data

	def __read_metadata(self, path: Path) -> Tuple[Metadata, List[str]]:
		with ZipFile(path) as archive:
			model = PluginMetadataJsonModel.model_validate_json(self.__read_archive_member(archive, plugin_constant.PLUGIN_META_FILE), strict=True)
			Version(model.version, allow_wildcard=False)  # Validation only: reject invalid versions before Metadata.create can fall back.
			metadata = Metadata.create(model)
			requirements: List[str] = []
			spec = metadata.requirements_file
			if spec.path is not None:
				try:
					data = self.__read_archive_member(archive, spec.path)
				except KeyError:
					if spec.mode is RequirementsFileSpec.Mode.REQUIRED:
						raise ValueError('Required requirements file {!r} is missing'.format(spec.path))
				else:
					for line in data.decode('utf8').splitlines():
						line = line.split('#', 1)[0].strip()
						if line:
							requirements.append(line)
			return metadata, requirements

	@staticmethod
	def __choose_file_name(names: Iterable[str], metadata: Metadata) -> str:
		# Reuse ASCII names only: letters/digits, underscore, dot, plus and hyphen.
		# Start with a letter/digit/underscore; keep the conservative 200-character/byte cap.
		# Windows reserved device names still apply to ASCII names:
		# https://learn.microsoft.com/en-us/windows/win32/fileio/naming-a-file
		for name in names:
			if (
				re.fullmatch(r'[A-Za-z0-9_][A-Za-z0-9._+-]{0,199}', name)
				and Path(name).suffix in plugin_constant.PACKED_PLUGIN_FILE_SUFFIXES
				and not re.fullmatch(r'CON|PRN|AUX|NUL|(?:COM|LPT)[1-9]', name.split('.')[0], re.IGNORECASE)
			):
				return name
		fallback = '{}-{}.mcdr'.format(metadata.id, metadata.version)
		return fallback if len(fallback) <= 200 else 'plugin-{}.mcdr'.format(metadata.id)
