import dataclasses
import enum
import os
import urllib.parse
import urllib.request
from pathlib import Path, PureWindowsPath
from typing import Optional, Union

from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.exceptions import SpecifierParseError
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.specifier_hash_parser import SpecifierHashParser


class UriScheme(enum.Enum):
	file = 'file'
	http = 'http'
	https = 'https'

	@classmethod
	def from_specifier(cls, raw: str) -> Optional['UriScheme']:
		scheme, separator, _ = raw.partition('://')
		if separator:
			try:
				return cls(scheme.lower())
			except ValueError:
				pass
		return None

	@property
	def is_remote(self) -> bool:
		return self is not UriScheme.file


@dataclasses.dataclass(frozen=True)
class UriPluginSpecifier:
	raw: str
	scheme: UriScheme
	location: Union[Path, urllib.parse.SplitResult]
	expected_sha256: Optional[str]

	@classmethod
	def parse(cls, raw: str, scheme: UriScheme) -> 'UriPluginSpecifier':
		uri, expected_hash = SpecifierHashParser.parse_uri(raw, is_remote=scheme.is_remote)
		location: Union[Path, urllib.parse.SplitResult]
		try:
			if scheme is UriScheme.file:
				location = cls.__parse_file_path(uri, scheme).absolute()
			else:
				location = urllib.parse.urlsplit(uri)
				if not location.hostname:
					raise ValueError('HTTP URI has no host')
				# Accessing port validates its syntax and range before downloading.
				_ = location.port
		except ValueError as e:
			raise SpecifierParseError('install.parse_specifier_failed', repr(raw), e) from e
		return cls(raw, scheme, location, expected_hash)

	@property
	def uri(self) -> str:
		if isinstance(self.location, Path):
			return self.location.as_uri()
		return self.location.geturl()

	@staticmethod
	def __parse_file_path(uri: str, scheme: UriScheme) -> Path:
		raw_path = uri[len(scheme.value + '://'):]
		if '?' in raw_path or '#' in raw_path:
			raise ValueError('file URI must not contain a query or fragment; percent-encode them in the path')
		# Accept the convenient file://D:\path and file://D:/path forms.
		native_path = PureWindowsPath(raw_path)
		if len(native_path.drive) == 2 and native_path.is_absolute():
			if os.name != 'nt':
				raise ValueError('Windows drive paths require Windows')
			return Path(urllib.parse.unquote(raw_path, errors='strict'))
		parts = urllib.parse.urlsplit(uri)
		if not parts.netloc or parts.netloc.lower() == 'localhost':
			path = parts.path
		else:
			# Preserve file://plugins/foo.mcdr as a relative path.
			path = parts.netloc + parts.path
		if not path:
			raise ValueError('file URI has no path')
		return Path(urllib.request.url2pathname(path))
