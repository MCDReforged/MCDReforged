import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from mcdreforged.handler.server_handler import ServerHandler
	from mcdreforged.plugin.type.plugin import AbstractPlugin


@dataclasses.dataclass(frozen=True)
class PluginProvidedServerHandlerHolder:
	server_handler: 'ServerHandler'
	plugin: 'AbstractPlugin'
