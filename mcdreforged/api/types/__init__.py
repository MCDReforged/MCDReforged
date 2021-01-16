"""
Type hints are always nice to have
"""
from mcdreforged.command.command_source import CommandSource, ConsoleCommandSource, PlayerCommandSource
from mcdreforged.info import Info
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.server_interface import ServerInterface

__all__ = [
	# Usually-used ones
	'ServerInterface', 'Info',
	'CommandSource', 'PlayerCommandSource', 'ConsoleCommandSource',
	'Metadata'
]
