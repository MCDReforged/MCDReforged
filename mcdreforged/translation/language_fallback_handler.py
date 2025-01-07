import dataclasses
import functools
from typing import Optional, Dict, List

from typing_extensions import Self

from mcdreforged.constants import core_constant


@dataclasses.dataclass(frozen=True)
class LanguageFallbackHandler:
	default_fallback: Optional[str]
	preferred_fallbacks: Dict[str, List[str]]

	def get_fallbacks(self, language: str) -> List[str]:
		fallbacks: List[str] = []
		fallbacks.extend(self.preferred_fallbacks.get(language, []))
		if self.default_fallback is not None:
			fallbacks.append(self.default_fallback)
		return fallbacks

	@classmethod
	@functools.lru_cache(maxsize=None)
	def none(cls) -> Self:
		return cls(default_fallback=None, preferred_fallbacks={})

	@classmethod
	def specified(cls, language: str) -> Self:
		return cls(default_fallback=language, preferred_fallbacks={})

	@classmethod
	@functools.lru_cache(maxsize=None)
	def auto(cls) -> Self:
		# hardcoding is ok for this
		return cls(default_fallback=core_constant.DEFAULT_LANGUAGE, preferred_fallbacks={
			'zh_tw': ['zh_cn'],
			'zh_cn': ['zh_tw'],
		})
