import re
import urllib.parse
from typing import Optional, Tuple

from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.exceptions import SpecifierParseError


class SpecifierHashParser:
	@classmethod
	def parse_specifier(cls, raw: str) -> Tuple[str, Optional[str]]:
		specifier, separator, suffix = raw.partition('@')
		if not separator:
			return raw, None
		suffix = suffix.lower()
		if re.fullmatch(r'[a-z0-9]+:[0-9abcdef]+', suffix) is not None:
			method, value = suffix.split(':', 1)
		else:
			method, value = 'sha256', suffix
		return specifier, cls.__validate_hash(raw, method, value)

	@classmethod
	def parse_uri(cls, raw: str, *, is_remote: bool) -> Tuple[str, Optional[str]]:
		# Split from the end so that user-info and other @ characters remain in the URI.
		uri, separator, suffix = raw.rpartition('@')
		if separator and re.fullmatch(r'[a-zA-Z0-9]+:[^/@?#]*', suffix):
			authority_end = raw.find('/', raw.find('://') + 3)
			# A numeric port in a pathless URL is part of the authority,
			# including when the host happens to be named after a hash method.
			if is_remote and authority_end < 0:
				try:
					if urllib.parse.urlsplit(raw).port is not None:
						return raw, None
				except ValueError:
					pass
			if not is_remote or suffix.lower().startswith('sha256:') or (0 <= authority_end < len(uri)):
				method, value = suffix.lower().split(':', 1)
				return uri, cls.__validate_hash(raw, method, value)
		return raw, None

	@staticmethod
	def __validate_hash(raw: str, method: str, value: str) -> str:
		if method != 'sha256':
			raise SpecifierParseError('install.hash_method_unsupported', repr(method))
		if re.fullmatch(r'[0-9abcdef]{10,64}', value) is None:
			raise SpecifierParseError('install.hash_validator_invalid', repr(raw))
		return value
