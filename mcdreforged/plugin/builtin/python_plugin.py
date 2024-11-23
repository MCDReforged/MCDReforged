import sys
from typing import TYPE_CHECKING

from typing_extensions import override

from mcdreforged.constants import core_constant
from mcdreforged.plugin.type.builtin_plugin import BuiltinPlugin

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager


def __get_python_version():
	version = '{}.{}.{}'.format(sys.version_info.major, sys.version_info.minor, sys.version_info.micro)
	if sys.version_info.releaselevel != 'final':
		version += '-{}.{}'.format(sys.version_info.releaselevel, sys.version_info.serial)
	return version


VERSION = __get_python_version()
METADATA = {
	'id': 'python',
	'version': VERSION,
	'name': 'Python {}'.format(VERSION),
	'author': 'Python Software Foundation',
	'link': 'https://www.python.org/'
}


class PythonPlugin(BuiltinPlugin):
	def __init__(self, plugin_manager: 'PluginManager'):
		super().__init__(plugin_manager, METADATA)

	@override
	def load(self):
		self.mcdr_server.logger.info(self.mcdr_server.translate('mcdreforged.python_plugin.info', core_constant.NAME, self.get_meta_name()))

	@override
	def _create_repr_fields(self) -> dict:
		return {'version': METADATA['version']}
