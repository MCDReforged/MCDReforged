from abc import ABC

from mcdreforged.plugin.plugin import AbstractPlugin


class PermanentPlugin(AbstractPlugin, ABC):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager, '**builtin**')

	def is_permanent(self) -> bool:
		return True

	def ready(self):
		pass

	def reload(self):
		pass

	def unload(self):
		pass

	def remove(self):
		pass