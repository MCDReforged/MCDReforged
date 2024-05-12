from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from mcdreforged.translation.translation_text import RTextMCDRTranslation


class Translator:
	def __init__(self, key_prefix: str):
		if key_prefix.startswith('.') or key_prefix.endswith('.'):
			raise ValueError(key_prefix)
		self.key_prefix = key_prefix

		from mcdreforged.plugin.si.server_interface import ServerInterface
		self.__si = ServerInterface.si()

	def create_child(self, sub_key: str) -> 'Translator':
		return Translator(self.key_prefix + '.' + sub_key)

	def __call__(self, key: str, *args, **kwargs) -> 'RTextMCDRTranslation':
		translation_key = self.key_prefix + '.' + key
		return self.__si.rtr(translation_key, *args, **kwargs)
