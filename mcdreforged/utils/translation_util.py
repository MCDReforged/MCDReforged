from typing import Optional

from mcdreforged.constants import core_constant
from mcdreforged.utils.types import TranslationKeyDictRich, MessageText, TranslationStorage, TranslationKeyDictNested

__all__ = [
	'translate_from_dict',
	'update_storage',
]

_NONE = object()


def translate_from_dict(translations: TranslationKeyDictRich, language: str, *, fallback_language: Optional[str] = core_constant.DEFAULT_LANGUAGE, default: Optional[MessageText] = _NONE) -> MessageText:
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


def update_storage(storage: TranslationStorage, language: str, mapping: TranslationKeyDictNested):
	__update_storage(storage, language, mapping)


def __update_storage(storage: TranslationStorage, language: str, mapping: TranslationKeyDictNested, path: Optional[str] = None):
	for key, item in mapping.items():
		current_path = f'{path}.{key}' if path is not None else key
		if isinstance(item, str):
			storage[current_path][language] = item
		elif isinstance(item, dict):
			__update_storage(storage, language, item, current_path)
