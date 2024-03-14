from typing import Optional, List, TYPE_CHECKING

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement
from mcdreforged.plugin.installer.meta_holder import MetaHolder
from mcdreforged.plugin.installer.plugin_installer import PluginInstaller
from mcdreforged.plugin.installer.replier import CommandSourceReplier
from mcdreforged.plugin.meta.version import VersionRequirement

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class PimCommand(SubCommand):
	def __init__(self, mcdr_plugin):
		super().__init__(mcdr_plugin)
		self.__meta_holder = MetaHolder()

	def get_command_node(self) -> Literal:
		def install_node() -> Literal:
			def plugin_id_node():
				# TODO
				return Text('plugin_id').configure(accumulate=True).suggests(lambda: [])

			node = Literal({'i', 'install'})
			node.runs(self.cmd_install_plugins)
			node.then(plugin_id_node().redirects(node))
			node.then(
				Literal({'-t', '--target'}).
				then(QuotableText('target').redirects(node))
			)
			node.then(
				CountingLiteral({'-u', '-U', '--upgrade'}, 'upgrade').
				redirects(node)
			)
			return node

		def freeze_node() -> Literal:
			node = Literal('freeze')
			node.runs(self.cmd_freeze)
			node.then(CountingLiteral({'-a', '--all'}, 'all').redirects(node))
			node.then(Literal({'-o', '--output'}).then(QuotableText('output').redirects(node)))
			return node

		def check_constraints_node() -> Literal:
			return Literal('check').runs(self.cmd_check_constraints)

		def list_node() -> Literal:
			node = Literal('list')
			node.runs(self.cmd_list_catalogue)
			node.then(QuotableText('keyword').runs(self.cmd_list_catalogue))
			return node

		def check_update_node() -> Literal:
			return Literal({'cu', 'check_update'})

		root = Literal('pim')
		root.then(install_node())
		root.then(freeze_node())
		root.then(check_constraints_node())
		root.then(check_update_node())
		root.then(list_node())
		return root

	@property
	def plugin_manager(self) -> 'PluginManager':
		return self.mcdr_plugin.plugin_manager

	def __create_installer(self, source: CommandSource):
		return PluginInstaller(
			CommandSourceReplier(source),
			language=source.get_preference().language,
			meta_holder=self.__meta_holder,
		)

	def cmd_freeze(self, source: CommandSource, context: CommandContext):
		if context.get('all'):
			plugins = self.plugin_manager.get_all_plugins()
		else:
			plugins = self.plugin_manager.get_regular_plugins()

		lines: List[str] = []
		for plugin in plugins:
			lines.append('{}=={}'.format(plugin.get_id(), plugin.get_metadata().version))

		if (output := context.get('output')) is not None:
			try:
				with open(output, 'w', encoding='utf8') as f:
					for line in lines:
						f.write(line)
						f.write('\n')
			except Exception as e:
				source.reply('freeze to file {!r} error: {}'.format(output, e))
				self.server_interface.logger.exception('pim freeze error', e)
			else:
				source.reply('freee to file {!r} done, exported {} plugins'.format(output, len(plugins)))
		else:
			for line in lines:
				source.reply(line)

	def cmd_list_catalogue(self, source: CommandSource, context: CommandContext):
		keyword = context.get('keyword')
		if keyword is not None:
			source.reply('Listing catalogue with keyword {!r}'.format(keyword))
		else:
			source.reply('Listing catalogue')
		plugin_installer = self.__create_installer(source)
		plugin_installer.list_plugin(keyword)

	def cmd_check_constraints(self, source: CommandSource, context: CommandContext):
		pass

	def cmd_install_plugins(self, source: CommandSource, context: CommandContext):
		plugin_ids: Optional[List[str]] = context.get('plugin_id')
		if not plugin_ids:
			source.reply('Please give some plugin id')
			return

		target: Optional[str] = context.get('target')
		if target is None and len(self.plugin_manager.plugin_directories) > 0:
			target = self.plugin_manager.plugin_directories[0]
		if target is None:
			source.reply('target is required')
			return
		do_upgrade = context.get('upgrade', 0) > 0

		source.reply('Plugins to installed: {}'.format(', '.join(plugin_ids)))
		source.reply('Target directory for installation: {!r}'.format(target))

		plugin_requirements: List[PluginRequirement] = []

		def add_requirement(plg: 'AbstractPlugin', op: str):
			plugin_requirements.append(PluginRequirement(
				id=plg.get_id(),
				requirement=VersionRequirement(op + str(plg.get_metadata().version))
			))

		try:
			input_requirements = list(map(PluginRequirement.of, plugin_ids))
		except ValueError as e:
			source.reply('req parse error: {}'.format(e))
			return
		for req in input_requirements:
			if (plugin := self.plugin_manager.get_plugin_from_id(req.id)) is None:
				plugin_requirements.append(req)
			else:
				if plugin.is_permanent():
					source.reply('cannot install permanent plugin')
					return
				if req.requirement.has_criterion():
					plugin_requirements.append(req)
				else:
					# pin unless upgrade
					if do_upgrade:
						add_requirement(plugin, '>=')
					else:
						add_requirement(plugin, '==')

		input_plugin_ids = {req.id for req in input_requirements}
		for plugin in self.plugin_manager.get_all_plugins():
			if plugin.get_id() not in input_plugin_ids:
				# pin for unselected plugins
				add_requirement(plugin, '==')

		for req in plugin_requirements:
			source.reply(str(req))
		plugin_installer = self.__create_installer(source)
		# TODO: tell resolver about local plugins (add xx==1.2.3)
		result = plugin_installer.resolve(plugin_requirements)
