import dataclasses
from typing import Optional, List

from typing_extensions import override

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal import pim_utils
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_base import PimCommandHandlerBase
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.plugin_requirement_source import PluginRequirementSource
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.texts import Texts
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, PluginDependencyResolver
from mcdreforged.plugin.meta.version import Version


class PimCheckUpdateCommandHandler(PimCommandHandlerBase):
	@override
	def process(self, source: CommandSource, context: CommandContext):
		if len(plugin_ids := context.get('plugin_id', [])) > 0:
			for plugin_id in plugin_ids:
				plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is None:
					source.reply(self._raw_tr('mcdr_command.invalid_plugin_id', plugin_id))
					return
			input_plugin_ids = set(plugin_ids)
		else:
			input_plugin_ids = {plugin.get_id() for plugin in self.plugin_manager.get_all_plugins()}

		plugin_requirements = []
		for plugin in self.plugin_manager.get_all_plugins():
			plugin_requirements.append(pim_utils.as_requirement(plugin, op='>=' if plugin.get_id() in input_plugin_ids else '=='))

		cata_meta = self.get_merged_cata_meta(source)
		resolver = PluginDependencyResolver(cata_meta)
		resolution = resolver.resolve(plugin_requirements)
		if isinstance(resolution, Exception):
			def req_src_getter(req: PluginRequirement):
				if req.id in input_plugin_ids:
					return PluginRequirementSource.existing
				else:
					return PluginRequirementSource.existing_pinned

			source.reply(self._tr('check_update.dependency_resolution_failed', resolution).set_color(RColor.red))
			pim_utils.show_resolve_error(source, resolution, self._tr, self.plugin_manager, req_src_getter=req_src_getter)
			return

		@dataclasses.dataclass(frozen=True)
		class UpdateEntry:
			id: str
			current_version: Version
			update_version: Version
			latest_version: Optional[Version]
			is_packed_plugin: bool

		# Possible cases:
		# - update-able (to latest version)
		# - update-able (to non-latest version, constraints not satisfied)
		# - not update-able (has newer version, constraints not satisfied)
		# - not update-able (has newer version, plugin not packed)
		# - already up-to-date

		update_able_plugins: List[UpdateEntry] = []
		not_update_able_plugins: List[UpdateEntry] = []
		up_to_date_plugins: List[UpdateEntry] = []

		from mcdreforged.plugin.type.packed_plugin import PackedPlugin
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			if plugin.is_builtin():
				continue

			is_packed_plugin = isinstance(plugin, PackedPlugin)
			current_version = plugin.get_version()
			latest_version = cata_meta[plugin_id].latest_version_parsed if plugin_id in cata_meta else None
			if latest_version is not None:
				latest_version = max(latest_version, current_version)
			entry = UpdateEntry(
				id=plugin_id,
				current_version=plugin.get_version(),
				update_version=version,
				latest_version=latest_version,
				is_packed_plugin=is_packed_plugin,
			)
			if current_version != version:
				if is_packed_plugin:
					update_able_plugins.append(entry)
				else:
					not_update_able_plugins.append(entry)
			elif latest_version is not None and latest_version != version:
				not_update_able_plugins.append(entry)
			else:
				up_to_date_plugins.append(entry)

		if len(update_able_plugins) + len(not_update_able_plugins) == 0:
			source.reply(self._tr('check_update.no_update.{}'.format('given' if plugin_ids else 'all'), len(input_plugin_ids)))
			return

		kinds = [
			(len(update_able_plugins), 'check_update.updatable.what'),
			(len(not_update_able_plugins), 'check_update.not_updatable.what'),
			(len(up_to_date_plugins), 'check_update.up_to_date.what'),
		]
		source.reply(self._tr(
			'check_update.found_summary',
			RTextBase.join(', ', [self._tr(k, Texts.number(n)) for n, k in kinds if n > 0])
		))

		if len(update_able_plugins) > 0:
			source.reply(self._tr('check_update.updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in update_able_plugins:
				# xxx 0.1.0 -> 0.2.0
				# xxx 0.1.0 -> 0.2.0 (latest: 0.3.0)
				texts = RTextList(
					pim_utils.INDENT,
					self.browse_cmd(entry.id),
					' ',
					RText(entry.current_version),
					RText(' -> ', RColor.gray),
					Texts.diff_version(entry.current_version, entry.update_version),
				)
				if entry.update_version != entry.latest_version:
					texts.append(
						' (',
						self._tr('check_update.latest', Texts.diff_version(entry.current_version, entry.latest_version)),
						')',
					)
				source.reply(texts)
			source.reply('')

		if len(not_update_able_plugins) > 0:
			source.reply(self._tr('check_update.not_updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in not_update_able_plugins:
				if entry.is_packed_plugin:
					reason = self._tr('check_update.not_updatable.reason.constraints_not_satisfied')
				else:
					reason = self._tr('check_update.not_updatable.reason.not_packed_plugin')
				# xxx 0.1.0 (latest 0.2.0) -- yyy reason
				source.reply(RTextList(
					pim_utils.INDENT,
					self.browse_cmd(entry.id),
					' ',
					RText(entry.current_version),
					' (',
					self._tr('check_update.latest', Texts.diff_version(entry.current_version, entry.latest_version)),
					') -- ',
					reason,
				))
			source.reply('')

		if len(update_able_plugins) > 0:
			source.reply(self._tr('check_update.updatable.hint1', Texts.cmd('!!MCDR plugin install -U ' + next(iter(update_able_plugins)).id)))
			source.reply(self._tr('check_update.updatable.hint2', Texts.cmd('!!MCDR plugin install -U *')))
	