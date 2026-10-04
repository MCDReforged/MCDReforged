import dataclasses
import enum
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path, PureWindowsPath
from typing import Optional, Tuple, Union


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
		uri, expected_hash = cls.__split_hash(raw, scheme)
		location: Union[Path, urllib.parse.SplitResult]
		if scheme is UriScheme.file:
			location = cls.__parse_file_path(uri, scheme).absolute()
		else:
			location = urllib.parse.urlsplit(uri)
			if not location.hostname:
				raise ValueError('HTTP URI has no host')
			# Accessing port validates its syntax and range before downloading.
			_ = location.port
		return cls(raw, scheme, location, expected_hash)

	@property
	def uri(self) -> str:
		if isinstance(self.location, Path):
			return self.location.as_uri()
		return self.location.geturl()

	@staticmethod
	def __split_hash(raw: str, scheme: UriScheme) -> Tuple[str, Optional[str]]:
		# <uri>[@sha256:<hash_hex>]
		# https://example.com/plugin.mcdr@sha256:abcdef0123
		# Split from the end so that user-info and other @ characters remain in the URI.
		uri, separator, suffix = raw.rpartition('@')
		if separator and re.fullmatch(r'[a-zA-Z0-9]+:[^/@?#]*', suffix):
			authority_end = raw.find('/', raw.find('://') + 3)
			# A numeric port in a pathless URL is part of the authority,
			# including when the host happens to be named after a hash method.
			if scheme.is_remote and authority_end < 0:
				try:
					if urllib.parse.urlsplit(raw).port is not None:
						return raw, None
				except ValueError:
					pass
			if scheme is UriScheme.file or suffix.lower().startswith('sha256:') or (authority_end >= 0 and len(uri) > authority_end):
				method, value = suffix.lower().split(':', 1)
				if method != 'sha256':
					raise ValueError('Unsupported hash method {!r}'.format(method))
				if re.fullmatch(r'[0-9abcdef]{10,64}', value) is None:
					raise ValueError('SHA256 validator must contain 10 to 64 hexadecimal characters')
				return uri, value
		return raw, None

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
