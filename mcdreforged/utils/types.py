from typing import Union, Dict

from mcdreforged.minecraft.rtext import RTextBase

MessageText = Union[str, RTextBase]
TranslationLanguageDict = Dict[str, str]  # language -> text
TranslationKeyDict = Dict[str, str]  # key -> text
TranslationKeyDictNested = Dict[str, Union[str, 'TranslationKeyDictNested']]  # key -> text/(key -> text/(...))
TranslationKeyDictRich = Dict[str, MessageText]  # language -> text
TranslationStorage = Dict[str, TranslationLanguageDict]  # key -> (language -> text)
