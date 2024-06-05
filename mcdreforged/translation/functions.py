from typing import TYPE_CHECKING

from typing_extensions import Protocol

if TYPE_CHECKING:
	from mcdreforged.translation.translation_text import RTextMCDRTranslation
	from mcdreforged.utils.types.message import MessageText


class TranslateFunc(Protocol):
	def __call__(self, key: str, *args, **kwargs) -> 'MessageText':
		...


class TranslateFuncR(Protocol):
	def __call__(self, key: str, *args, **kwargs) -> 'RTextMCDRTranslation':
		...
