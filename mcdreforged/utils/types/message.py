from typing import Union, Dict, TYPE_CHECKING, Mapping

if TYPE_CHECKING:
	from mcdreforged.minecraft.rtext.text import RTextBase


MessageText = Union[str, 'RTextBase']
TranslationLanguageDict = Dict[str, str]  # language -> text
TranslationKeyDict = Dict[str, str]  # key -> text
TranslationKeyDictNested = Dict[str, Union[str, 'TranslationKeyDictNested']]  # key -> text/(key -> text/(...))
TranslationKeyDictRich = Dict[str, MessageText]  # language -> text
TranslationKeyMapping = Mapping[str, str]  # key -> text
TranslationKeyMappingNested = Mapping[str, Union[str, 'TranslationKeyDictNested']]  # key -> text/(key -> text/(...))
TranslationKeyMappingRich = Mapping[str, MessageText]  # language -> text
TranslationStorage = Dict[str, TranslationLanguageDict]  # key -> (language -> text)
