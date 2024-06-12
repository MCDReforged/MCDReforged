from typing import Optional

from mcdreforged.constants import core_constant
from mcdreforged.utils.types.message import TranslationKeyDictRich, MessageText, TranslationStorage, TranslationKeyDictNested, TranslationKeyDict

__all__ = [
	'translate_from_dict',
	'update_storage',
]

_NONE = object()


def get_mcdr_language() -> str:
	from mcdreforged.plugin.si.server_interface import ServerInterface
	server: Optional[ServerInterface] = ServerInterface.get_instance()
	if server is not None:
		language = server.get_mcdr_language()
	else:
		language = core_constant.DEFAULT_LANGUAGE
	return language


def translate_from_dict(
		translations: TranslationKeyDictRich, language: str,
		*,
		fallback_language: Optional[str] = core_constant.DEFAULT_LANGUAGE, default: Optional[MessageText] = _NONE
) -> MessageText:
	"""
	Select a translation for given language based on a translation dict
	:param language: The language
	:param fallback_language: If translation file, it will try using the fallback_language as language for a second try
	:param translations: A language -> text mapping
	:param default: The fallback value. If not specified and translation not found, KeyError will be risen
	"""
	result = translations.get(language)
	if result is None and fallback_language is not None:
		result = translations.get(fallback_language)
	if result is None:
		result = default
	if result is _NONE:
		raise KeyError('Failed to translate from dict with translations {}, language {}, fallback_language {}'.format(translations, language, fallback_language))
	return result


def unpack_nest_translation(translation: TranslationKeyDictNested) -> TranslationKeyDict:
	def traverse(mapping: TranslationKeyDictNested, path: str = ''):
		for key, value in mapping.items():
			if not isinstance(key, str):
				raise ValueError('bad key type at {!r}, should be str: ({}) {}'.format(path, type(key), key))
			if key == '.':
				current_path = path
			else:
				current_path = key if path == '' else path + '.' + key
			if isinstance(value, str):
				result[current_path] = value
			elif isinstance(value, dict):
				traverse(value, current_path)
			else:
				raise ValueError('bad value type at {!r}, should be str or dict: ({}) {}'.format(current_path, type(value), value))

	result = {}
	traverse(translation, '')
	return result


def update_storage(storage: TranslationStorage, language: str, mapping: TranslationKeyDictNested):
	for key, value in unpack_nest_translation(mapping).items():
		storage[key][language] = value


def extend_storage(translations: TranslationStorage, other: TranslationStorage):
	for key, lang_dict in other.items():
		if key not in translations:
			translations[key] = lang_dict.copy()
		else:
			translations[key].update(lang_dict)
