from mcdreforged import constant
from mcdreforged.plugin.metadata import MetaData
from mcdreforged.plugin.plugin import BuiltinPlugin

METADATA = {
	'id': constant.NAME.lower(),
	'version': constant.VERSION,
	'name': constant.NAME,
	'description': 'The Core of {}'.format(constant.NAME),
	'author': [
		'Fallen_Breath'
	],
	'link': 'https://github.com/Fallen-Breath/MCDReforged'
}


class MCDReforgedPlugin(BuiltinPlugin):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager)
		self.metadata = MetaData(self, METADATA)

	def is_permanent(self) -> bool:
		return True

	def get_metadata(self) -> MetaData:
		return self.metadata

	def get_fallback_metadata_id(self) -> str:
		return METADATA['id']

	def load(self):
		pass

	def ready(self):
		pass

	def reload(self):
		pass

	def unload(self):
		pass

	def remove(self):
		pass
