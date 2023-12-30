from typing import NamedTuple, TYPE_CHECKING

if TYPE_CHECKING:
	from mcdreforged.handler.server_handler import ServerHandler
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class PluginProvidedServerHandlerHolder(NamedTuple):
	server_handler: 'ServerHandler'
	plugin: 'AbstractPlugin'
