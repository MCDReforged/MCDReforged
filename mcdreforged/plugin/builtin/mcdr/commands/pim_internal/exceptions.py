from typing import Any


class OuterReturn(Exception):
	pass


class SpecifierParseError(ValueError):
	def __init__(self, translation_key: str, *translation_args: Any):
		super().__init__(translation_key)
		self.translation_key = translation_key
		self.translation_args = translation_args
