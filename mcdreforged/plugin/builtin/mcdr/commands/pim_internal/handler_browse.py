from typing_extensions import override

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor, RAction
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_base import PimCommandHandlerBase
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.texts import Texts
from mcdreforged.plugin.installer.catalogue_access import PluginCatalogueAccess
from mcdreforged.plugin.installer.types import MetaRegistry, ReleaseData
from mcdreforged.utils.replier import CommandSourceReplier


class PimBrowseCommandHandler(PimCommandHandlerBase):
	@override
	def process(self, source: CommandSource, context: CommandContext):
		cata_meta = self.get_cata_meta(source)

		if (plugin_id := context.get('plugin_id')) is not None:
			self.__browse_one(source, context, cata_meta, plugin_id)
		else:
			self.__browse_all(source, context, cata_meta)

	def __browse_one(self, source: CommandSource, _: CommandContext, cata_meta: MetaRegistry, plugin_id: str):
		plugin_data = cata_meta.plugins.get(plugin_id)
		if plugin_data is None:
			source.reply('Plugin with id {} does not exist in the catalogue'.format(plugin_id))
			return

		na = RText('N/A', color=RColor.gray)
		source.reply(self._tr('browse.single.id', Texts.plugin_id(plugin_data.id)))
		source.reply(self._tr('browse.single.name', plugin_data.name or na))
		source.reply(self._tr('browse.single.description', plugin_data.description_for(source.get_preference().language) or na))
		source.reply(self._tr(
			'browse.single.repository',
			Texts.url(plugin_data.repos_pair, plugin_data.repos_url, underlined=False).
			h(self._tr('browse.single.url', Texts.url(plugin_data.repos_url, plugin_data.repos_url)))
		))

		if len(plugin_data.releases) > 0 and plugin_data.latest_version is not None:
			def version_text(r: ReleaseData, anchor: bool) -> RTextBase:
				text = RTextList(
					Texts.version(r.version).
					c(RAction.suggest_command, '!!MCDR plugin install {}=={}'.format(plugin_id, r.version)).
					h(RTextBase.join('\n', [
						self._tr('browse.single.version', Texts.version(r.version)),
						self._tr('browse.single.date', r.created_at.strftime('%Y-%m-%d %H:%M:%S')),
					]))
				)
				if anchor:
					text.append(
						RText('*', color=RColor.blue).
						c(RAction.open_url, r.url).
						h(self._tr('browse.single.url', Texts.url(r.url, r.url)))
					)
				return text

			latest = plugin_data.releases[plugin_data.latest_version]
			source.reply(self._tr(
				'browse.single.latest_version',
				version_text(latest, False),
			))
			versions = []
			for release in plugin_data.releases.values():
				versions.append(version_text(release, True))

			source.reply(self._tr('browse.single.releases', len(plugin_data.releases)))
			for i in range(0, len(versions), 10):
				line = RTextBase.join(', ', [versions[j] for j in range(i, min(i + 10, len(versions)))])
				source.reply(line)

	def __browse_all(self, source: CommandSource, context: CommandContext, cata_meta: MetaRegistry):
		keyword = context.get('keyword')
		if keyword is not None:
			source.reply(self._tr('browse.all.keyword', keyword))

		if source.is_player:
			# table does not display well in mc chat hud
			plugins = PluginCatalogueAccess.filter_sort(cata_meta.plugins.values(), keyword)
			for plg in plugins:
				source.reply(RTextList(
					self.browse_cmd(plg.id).h(plg.name),
					RText(': ', RColor.gray),
					plg.description_for(source.get_preference().language)
				))
			if len(plugins) == 0:
				source.reply(self._tr('browse.all.empty'))
		else:
			with source.preferred_language_context():  # required for table formatting
				cnt = PluginCatalogueAccess.list_plugin(
					meta=cata_meta,
					replier=CommandSourceReplier(source),
					keyword=keyword,
					table_header=(
						self._tr('browse.all.title.id'),
						self._tr('browse.all.title.name'),
						self._tr('browse.all.title.version'),
						self._tr('browse.all.title.description'),
					),
				)
			if cnt == 0:
				source.reply(self._tr('browse.all.empty'))
