from typing import NamedTuple


class Deprecation(NamedTuple):
	feature: str
	version_deprecated: str
	version_removal: str

	def __str__(self):
		return '{} is deprecated in v{}, and will be removed in v{}'.format(self.feature.capitalize(), self.version_deprecated, self.version_removal)


PLUGIN_ID_STARTS_WITH_NON_ALPHABET = Deprecation('plugin id starting with non-alphabet letter', '2.11.0', '2.13')
SERVER_INTERFACE_LANGUAGE_KEYWORD = Deprecation('ServerInterface.tr language as non-translation-keyword argument', '2.12.0', '2.15')
