"""
Type hints are always nice to have
"""
from mcdreforged.command.command_source import CommandSource, ConsoleCommandSource, PlayerCommandSource, \
	InfoCommandSource, PluginCommandSource
from mcdreforged.info import Info
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.server_interface import ServerInterface

__all__ = [
	# Usually-used ones
	'ServerInterface', 'Info',

	# Command sources
	'CommandSource', 'InfoCommandSource', 'PlayerCommandSource', 'ConsoleCommandSource', 'PluginCommandSource',

	# Plugin things
	'Metadata',

	# Permission
	'PermissionLevel',
]
