from typing import Optional, TYPE_CHECKING, Callable

import resolvelib

from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.plugin_requirement_source import PluginRequirementSource
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement
from mcdreforged.plugin.meta.version import VersionRequirement
from mcdreforged.translation.translator import Translator

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.plugin import AbstractPlugin


INDENT = ' ' * 4
CONFIRM_WAIT_TIMEOUT = 60  # seconds


def as_requirement(plugin: 'AbstractPlugin', op: Optional[str], **kwargs) -> PluginRequirement:
	if op is not None:
		req = op + str(plugin.get_version())
	else:
		req = ''
	return PluginRequirement(
		id=plugin.get_id(),
		requirement=VersionRequirement(req),
		**kwargs,
	)


def show_resolve_error(
		source: 'CommandSource', err: Exception,
		pim_tr: Translator, plugin_manager: 'PluginManager',
		*,
		req_src_getter: Optional[Callable[[PluginRequirement], 'PluginRequirementSource']] = None
):
	if req_src_getter is None:
		req_src_getter = {}.get
	if isinstance(err, resolvelib.ResolutionImpossible):
		source.reply(pim_tr('install.resolution.impossible'))
		source.reply('')
		showed_causes = set()
		for cause in err.causes:
			if cause in showed_causes:
				continue
			showed_causes.add(cause)
			cause_req: PluginRequirement = cause.requirement
			req_src = req_src_getter(cause_req)
			if cause.parent is not None or req_src is None:
				source.reply(INDENT + pim_tr('install.resolution.impossible_requirements', cause.parent, cause_req))
			else:
				args = ()
				if req_src == PluginRequirementSource.user_input:
					args = (cause_req,)
				elif req_src in [PluginRequirementSource.existing, PluginRequirementSource.existing_pinned]:
					plugin = plugin_manager.get_plugin_from_id(cause_req.id)
					args = (plugin.get_id(), plugin.get_version())
				source.reply(INDENT + pim_tr('install.resolution.source_reason.' + req_src.name, *args))
		source.reply('')
	else:
		source.reply(pim_tr('install.resolution.error', err))
