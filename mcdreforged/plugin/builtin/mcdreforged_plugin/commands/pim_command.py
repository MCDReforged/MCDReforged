import contextlib
import os
import shutil
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Dict, Set

import resolvelib
from typing_extensions import override

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, DependencyResolver
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.meta_holder import MetaHolder
from mcdreforged.plugin.installer.plugin_installer import PluginInstaller
from mcdreforged.plugin.installer.replier import CommandSourceReplier
from mcdreforged.plugin.installer.types import MetaCache, PluginData, ReleaseData, ChainMetaCache
from mcdreforged.plugin.meta.version import VersionRequirement

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class LocalMetaCache(MetaCache):
	def __init__(self, plugin_manager: 'PluginManager', cache: bool = True):
		self.__plugin_manager = plugin_manager
		self.__do_cache = cache
		self.__cached_data: Optional[dict] = None

	@override
	@property
	def plugins(self) -> Dict[str, PluginData]:
		if self.__do_cache and self.__cached_data is not None:
			return self.__cached_data

		result = {}
		for plugin in self.__plugin_manager.get_all_plugins():
			meta = plugin.get_metadata()
			version = str(meta.version)
			result[meta.id] = PluginData(
				id=meta.id,
				name=meta.name,
				latest_version=version,
				description=meta.description,
				releases={version: ReleaseData(
					version=version,
					dependencies={},
					requirements=[],
					file_name=plugin.plugin_path,
					file_size=0,
					file_url=f'file://' + plugin.plugin_path,
					file_sha256='',
				)}
			)
		if self.__do_cache:
			self.__cached_data = result
		return result


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
		default_target_path = Path(target)
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
			source.reply('REQ: ' + str(req))

		cata_meta = self.__meta_holder.get()
		resolver = DependencyResolver(ChainMetaCache(cata_meta,LocalMetaCache(self.plugin_manager)))
		ret = resolver.resolve(plugin_requirements)

		if isinstance(ret, Exception):
			err = ret
			if isinstance(err, resolvelib.ResolutionImpossible):
				source.reply('ResolutionImpossible!')
				for cause in err.causes:
					source.reply('    {} requires {}'.format(cause.parent, cause.requirement))
			else:
				source.reply('Resolution error: {}'.format(err))
			return

		resolution = ret
		for plugin_id, version in resolution.items():
			source.reply('RES: {} {}'.format(plugin_id, version))

		# collect
		to_install: Dict[str, ReleaseData] = {}
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			if plugin is not None:
				old_ver = plugin.get_metadata().version
			else:
				old_ver = None
			if old_ver != version:
				source.reply('INS: {} {} -> {}'.format(plugin_id, old_ver, version))
				try:
					to_install[plugin_id] = cata_meta.plugins[plugin_id].releases[str(version)]
				except KeyError:
					# TODO: proper error dump
					raise AssertionError('unexpected to-install plugin {} version {}'.format(plugin_id, version))

		if len(to_install) == 0:
			source.reply('Nothing is needed to be installed')
			return

		for plugin_id in to_install.keys():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			from mcdreforged.plugin.type.packed_plugin import PackedPlugin
			if not isinstance(plugin, PackedPlugin):
				source.reply('Existing plugin {} is {} and cannot be reinstalled. Only packed plugin is supported'.format(plugin_id, type(plugin).__name__))
				return
		# TODO: confirm

		# download
		download_temp_dir = Path(self.server_interface.get_data_folder()) / 'pim_{}'.format(os.getpid())  # todo: better dir name
		if download_temp_dir.is_dir():
			shutil.rmtree(download_temp_dir)
		path_mapping: Dict[str, Path] = {}
		existing_names: Set[str] = set()
		with contextlib.ExitStack() as es:
			def clean_up():
				if download_temp_dir.is_dir():
					shutil.rmtree(download_temp_dir)
			es.callback(clean_up)
			# TODO: rollback-able

			for plugin_id, release in to_install.items():
				file_name = release.file_name  # TODO: sanitize file name
				if file_name in existing_names:
					raise ValueError()  # TODO: rename
				existing_names.add(file_name)
				temp_path = download_temp_dir / file_name
				path_mapping[plugin_id] = temp_path
				source.reply('Downloading {}@{}'.format(plugin_id, release.version))
				ReleaseDownloader(release, temp_path, CommandSourceReplier(source)).download()

			# apply
			for plugin_id, release in to_install.items():
				plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is not None:
					path = Path(plugin.plugin_path)
					target_dir = path.parent
					source.reply('!! removing {}@{} at {}'.format(plugin_id, plugin.get_metadata().version, path))
					path.unlink(missing_ok=True)
				else:
					target_dir = default_target_path

				src = path_mapping[plugin_id]
				dst = target_dir / src.name  # TODO: fix file collision
				source.reply('Installing {}@{} to {}'.format(plugin_id, release.version, dst))
				shutil.move(src, dst)

			# reload
			# TODO: add api: batch_manipulate_plugins
			source.reply('Reloading MCDR')
			self.server_interface.refresh_changed_plugins()
			source.reply('done')

