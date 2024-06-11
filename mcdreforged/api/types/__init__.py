"""
Type hints are always nice to have
"""
from mcdreforged.command.command_source import CommandSource, ConsoleCommandSource, PlayerCommandSource, \
	InfoCommandSource, PluginCommandSource
from mcdreforged.info_reactor.info import Info
from mcdreforged.info_reactor.info_filter import InfoFilter
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.meta.metadata import Metadata
from mcdreforged.plugin.meta.version import Version, VersionRequirement
from mcdreforged.plugin.si.plugin_server_interface import PluginServerInterface
from mcdreforged.plugin.si.server_interface import ServerInterface
from mcdreforged.plugin.type.common import PluginFormat
from mcdreforged.preference.preference_manager import PreferenceItem
from mcdreforged.utils.logger import SyncStdoutStreamHandler, MCDReforgedLogger


__all__ = [
	# Server interfaces
	'ServerInterface', 'PluginServerInterface',

	# Info
	'Info', 'InfoFilter',

	# Server stuffs
	'ServerInformation',

	# Command sources
	'CommandSource', 'InfoCommandSource', 'PlayerCommandSource', 'ConsoleCommandSource', 'PluginCommandSource',

	# Plugin things
	'Metadata', 'Version', 'VersionRequirement', 'PluginFormat',

	# Permission
	'PermissionLevel',

	# Preference
	'PreferenceItem',

	# Logging
	'SyncStdoutStreamHandler', 'MCDReforgedLogger'
]
