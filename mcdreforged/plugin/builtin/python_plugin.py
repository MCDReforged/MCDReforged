import sys

from mcdreforged.constants import core_constant
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.type.permanent_plugin import PermanentPlugin


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


class PythonPlugin(PermanentPlugin):
	def __init__(self, plugin_manager):
		super().__init__(plugin_manager)
		self._set_metadata(Metadata(METADATA, plugin=self))

	def load(self):
		self.mcdr_server.logger.info(self.mcdr_server.tr('python_plugin.info', core_constant.NAME, self.get_meta_name()))

	def __repr__(self):
		return 'PythonPlugin[version={}]'.format(METADATA['version'])
