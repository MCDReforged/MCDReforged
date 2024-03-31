import dataclasses
import enum
import functools
import logging
import os
import re
import shutil
import subprocess
import threading
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Dict, NamedTuple

import resolvelib
from typing_extensions import override, deprecated

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants.core_constant import DEFAULT_LANGUAGE
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, PluginDependencyResolver, PackageRequirementResolver
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.meta_holder import AsyncPersistCatalogueMetaRegistryHolder
from mcdreforged.plugin.installer.plugin_installer import PluginCatalogueAccess
from mcdreforged.plugin.installer.replier import CommandSourceReplier
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData, MergedMetaRegistry
from mcdreforged.plugin.meta.version import VersionRequirement, Version
from mcdreforged.utils import misc_util

if TYPE_CHECKING:
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.plugin import AbstractPlugin


class LocalReleaseData(ReleaseData):
	pass


class LocalMetaRegistry(MetaRegistry):
	def __init__(self, plugin_manager: 'PluginManager', cache: bool = True):
		self.__plugin_manager = plugin_manager
		self.__do_cache = cache
		self.__cached_data: Optional[dict] = None

	@property
	@override
	def plugins(self) -> Dict[str, PluginData]:
		if self.__do_cache and self.__cached_data is not None:
			return self.__cached_data

		result = {}
		for plugin in self.__plugin_manager.get_all_plugins():
			meta = plugin.get_metadata()
			version = str(meta.version)
			if isinstance(meta.description, str):
				description = {DEFAULT_LANGUAGE: meta.description}
			elif isinstance(meta.description, dict):
				description = meta.description.copy()
			else:
				description = {}
			result[meta.id] = PluginData(
				id=meta.id,
				name=meta.name,
				repos_owner='',
				repos_name='',
				latest_version=version,
				description=description,
				releases={version: LocalReleaseData(
					version=version,
					tag_name='',
					dependencies={},
					requirements=[],
					asset_id=0,
					file_name='',
					file_size=0,
					file_url='',
					file_sha256='',
				)}
			)
		if self.__do_cache:
			self.__cached_data = result
		return result


def as_requirement(plugin: 'AbstractPlugin', op: Optional[str]) -> PluginRequirement:
	if op is not None:
		req = op + str(plugin.get_metadata().version)
	else:
		req = ''
	return PluginRequirement(
		id=plugin.get_id(),
		requirement=VersionRequirement(req)
	)


def sanitize_filename(filename: str) -> str:
	return re.sub(r'[\\/*?"<>|:]', '_', filename.strip())


@dataclasses.dataclass
class OperationHolder:
	lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)
	thread: threading.Thread = dataclasses.field(default=None)


def async_operation(op_holder: OperationHolder, skip_callback: callable, thread_name: str):
	def decorator(op_key: str):
		def func_transformer(func: callable):
			@functools.wraps(func)
			def wrapped_func(*args, **kwargs):
				acquired = op_holder.lock.acquire(blocking=False)
				if acquired:
					def run():
						try:
							func(*args, **kwargs)
						finally:
							op_holder.operation_thread = None
							op_holder.lock.release()
					try:
						thread = threading.Thread(target=run, name=thread_name)
						thread.start()
						op_holder.operation_thread = thread
						return thread
					except BaseException:
						op_holder.lock.release()
						raise
				else:
					skip_callback(*args, op_func=wrapped_func, op_key=op_key, op_thread=op_holder.operation_thread, **kwargs)

			misc_util.copy_signature(wrapped_func, func)
			return wrapped_func
		return func_transformer
	return decorator


class ConfirmHelperState(enum.Enum):
	none = enum.auto()  # pre-waiting
	waiting = enum.auto()  # waiting
	confirmed = enum.auto()  # post-waiting
	aborted = enum.auto()  # post-waiting
	cancelled = enum.auto()  # post-waiting (abort silently)


class ConfirmHelper:
	def __init__(self):
		self.__lock = threading.Lock()
		self.__event = threading.Event()
		self.__state = ConfirmHelperState.none

	def wait(self, timeout: float) -> bool:
		with self.__lock:
			self.__state = ConfirmHelperState.waiting
		return self.__event.wait(timeout=timeout)

	def set(self, state: ConfirmHelperState):
		with self.__lock:
			if self.__state == ConfirmHelperState.waiting:
				self.__state = state
				self.__event.set()

	def get(self) -> ConfirmHelperState:
		with self.__lock:
			return self.__state

	def clear(self):
		with self.__lock:
			self.__event.clear()
			self.__state = ConfirmHelperState.none


class PluginCommandPimExtension(SubCommand):
	CONFIRM_WAIT_TIMEOUT = 60  # seconds
	current_operation = OperationHolder()

	def __init__(self, mcdr_plugin):
		super().__init__(mcdr_plugin)
		self.__meta_holder = AsyncPersistCatalogueMetaRegistryHolder(
			self.mcdr_server.logger,
			Path(self.server_interface.get_data_folder()) / 'catalogue_meta_cache.json.xz',
			meta_json_url=self.mcdr_server.config.catalogue_meta_url,
			meta_fetch_timeout=self.mcdr_server.config.catalogue_meta_fetch_timeout,
		)
		self.__installation_confirm_helper = ConfirmHelper()
		self.__installation_source: Optional[CommandSource] = None

	@override
	@deprecated('use get_command_child_nodes instead')
	def get_command_node(self) -> Literal:
		raise NotImplementedError()

	def get_command_child_nodes(self) -> List[Literal]:
		def install_node() -> Literal:
			def suggest_plugin_id():
				keys = set(self.__meta_holder.get_registry().plugins.keys())
				keys.add('*')  # for update all
				return keys

			node = Literal('install')
			node.runs(self.cmd_install_plugins)
			node.then(
				Text('plugin_requirement').configure(accumulate=True).
				suggests(suggest_plugin_id).
				redirects(node)
			)
			node.then(
				Literal({'-t', '--target'}).
				then(QuotableText('target').redirects(node))
			)
			node.then(CountingLiteral({'-u', '--update'}, 'update').redirects(node))
			node.then(CountingLiteral('--dry-run', 'dry_run').redirects(node))
			node.then(CountingLiteral({'-y', '--yes'}, 'skip_confirm').redirects(node))
			return node

		def freeze_node() -> Literal:
			node = Literal('freeze')
			node.runs(self.cmd_freeze)
			node.then(CountingLiteral({'-a', '--all'}, 'all').redirects(node))
			return node

		def validate_constraints_node() -> Literal:
			return Literal('validate').runs(self.cmd_validate_constraints)

		def browse_node() -> Literal:
			node = Literal('browse')
			node.runs(self.cmd_browse_catalogue)
			node.then(QuotableText('keyword').runs(self.cmd_browse_catalogue))
			return node

		def check_update_node() -> Literal:
			node = Literal({'checkupdate', 'cu'})
			node.runs(self.cmd_check_update)
			node.then(
				Text('plugin_id').configure(accumulate=True).
				suggests(lambda: [plg.get_id() for plg in self.plugin_manager.get_regular_plugins()]).
				redirects(node)
			)
			return node

		def refresh_meta_node() -> Literal:
			node = Literal('refresh_meta')
			node.runs(self.cmd_refresh_meta)
			return node

		return [
			browse_node(),
			check_update_node(),
			freeze_node(),
			install_node(),
			refresh_meta_node(),
			validate_constraints_node(),
		]

	@override
	def on_load(self):
		self.__meta_holder.init()

	@override
	def on_mcdr_stop(self):
		self.__installation_confirm_helper.set(ConfirmHelperState.aborted)
		thread = self.current_operation.thread
		if thread is not None:
			thread.join(timeout=self.CONFIRM_WAIT_TIMEOUT + 1)

	@override
	def on_event(self, source: Optional[CommandSource], event: SubCommandEvent) -> bool:
		sis = self.__installation_source
		if event == SubCommandEvent.confirm:
			if sis is not None and source == sis:
				self.__installation_confirm_helper.set(ConfirmHelperState.confirmed)
				return True
		elif event == SubCommandEvent.abort:
			if sis is not None and source is not None and source.get_permission_level() >= sis.get_permission_level():
				self.__installation_confirm_helper.set(ConfirmHelperState.aborted)
				return True
		return False

	@property
	def logger(self) -> logging.Logger:
		return self.server_interface.logger

	@property
	def plugin_manager(self) -> 'PluginManager':
		return self.mcdr_plugin.plugin_manager

	def get_cata_meta(self, source: CommandSource) -> MetaRegistry:
		def fetch_callback():
			source.reply('Fetching plugin catalogue meta')
		return self.__meta_holder.get_registry(fetch_callback=fetch_callback)

	def __create_installer(self, source: CommandSource):
		return PluginCatalogueAccess(
			CommandSourceReplier(source),
			meta_holder=self.__meta_holder,
			meta_json_url=self.mcdr_server.config.catalogue_meta_url,
			meta_fetch_timeout=self.mcdr_server.config.catalogue_meta_fetch_timeout,
		)

	def __handle_duplicated_input(self, source: CommandSource, context: CommandContext, op_func: callable, op_key: str, op_thread: Optional[threading.Thread]):
		if op_func == type(self).cmd_install_plugins:
			sis = self.__installation_source
			if sis is not None and sis == source:
				# Another installation command when waiting for installation
				# Cancel the existing one and perform another installation
				self.__installation_confirm_helper.set(ConfirmHelperState.cancelled)
				if op_thread is not None:
					op_thread.join(1)
					if op_thread.is_alive():
						self.logger.error('Join thread {} failed, skipped new installation operation'.format(op_thread))
						return
				self.cmd_install_plugins(source, context)
				return
		source.reply('Dont Spam, current op {} {}'.format(op_func, op_key))

	plugin_installer_guard = async_operation(op_holder=current_operation, skip_callback=__handle_duplicated_input, thread_name='PluginInstaller')

	@plugin_installer_guard('browse')
	def cmd_browse_catalogue(self, source: CommandSource, context: CommandContext):
		keyword = context.get('keyword')
		if keyword is not None:
			source.reply('Listing catalogue with keyword {!r}'.format(keyword))
		else:
			source.reply('Listing catalogue')
		plugin_installer = self.__create_installer(source)
		plugin_installer.list_plugin(keyword)

	@plugin_installer_guard('validate')
	def cmd_validate_constraints(self, source: CommandSource, context: CommandContext):
		plugin_requirements = list(map(
			functools.partial(as_requirement, op='=='),
			self.plugin_manager.get_all_plugins()
		))
		resolver = PluginDependencyResolver(LocalMetaRegistry(self.plugin_manager))
		ret = resolver.resolve(plugin_requirements)
		if isinstance(ret, Exception):
			source.reply('failed: {}'.format(ret))
		else:
			source.reply('success')

	@plugin_installer_guard('check_update')
	def cmd_check_update(self, source: CommandSource, context: CommandContext):
		if len(plugin_ids := context.get('plugin_id', [])) > 0:
			plugins = []
			for plugin_id in plugin_ids:
				plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is None:
					source.reply(self.tr('mcdr_command.invalid_plugin_id', plugin_id))
				plugins.append(plugin)
		else:
			plugins = self.plugin_manager.get_all_plugins()

		plugin_requirements = [as_requirement(plugin, op='>=') for plugin in plugins]
		resolver = PluginDependencyResolver(MergedMetaRegistry(self.get_cata_meta(source), LocalMetaRegistry(self.plugin_manager)))
		resolution = resolver.resolve(plugin_requirements)
		if isinstance(resolution, Exception):
			source.reply('failed: {}'.format(resolution))
			return

		update_able_plugins = []
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			old_version = plugin.get_metadata().version
			if old_version != version:
				from mcdreforged.plugin.type.packed_plugin import PackedPlugin
				update_able_plugins.append((plugin_id, old_version, version, isinstance(plugin, PackedPlugin)))

		if len(update_able_plugins) == 0:
			source.reply('No updates found for {} installed plugins'.format(len(plugin_requirements)))
			return

		source.reply('Found {} plugins with update'.format(len(update_able_plugins)))
		for plugin_id, old_version, new_version, is_packed_plugin in update_able_plugins:
			source.reply('  {} {} -> {} (can: {})'.format(plugin_id, old_version, new_version, is_packed_plugin))

	def cmd_freeze(self, source: CommandSource, context: CommandContext):
		if context.get('all', 0) > 0:
			source.reply('Freezing all plugins in plugin requirement format')
			plugins = self.plugin_manager.get_all_plugins()
		else:
			source.reply('Freezing installed plugins in plugin requirement format')
			plugins = self.plugin_manager.get_regular_plugins()

		lines: List[str] = []
		for plugin in plugins:
			lines.append('{}=={}'.format(plugin.get_id(), plugin.get_metadata().version))

		for line in lines:
			source.reply(line)

	def cmd_refresh_meta(self, source: CommandSource, context: CommandContext):
		def callback(e: Optional[Exception]):
			if e is None:
				source.reply('Meta fetch done')
			else:
				source.reply('Meta fetch failed: {}'.format(e))

		triggered = self.__meta_holder.async_fetch(ignore_cache=True, callback=callback)
		if triggered:
			source.reply('Meta fetch triggered')
		else:
			source.reply('Meta fetching already')

	@plugin_installer_guard('install')
	def cmd_install_plugins(self, source: CommandSource, context: CommandContext):
		# ------------------- Prepare -------------------
		input_requirement_strings: Optional[List[str]] = context.get('plugin_requirement')
		if not input_requirement_strings:
			source.reply('Please give some plugin specifier')
			return

		target: Optional[str] = context.get('target')
		if target is None:
			if len(self.plugin_manager.plugin_directories) > 0:
				default_target_path = self.plugin_manager.plugin_directories[0]
			else:
				source.reply('target is required')
				return
		else:
			default_target_path = Path(target)
		do_update = context.get('update', 0) > 0
		dry_run = context.get('dry_run', 0) > 0
		skip_confirm = context.get('skip_confirm', 0) > 0

		# ------------------- Verify and Collect -------------------

		from mcdreforged.plugin.type.packed_plugin import PackedPlugin

		def add_requirement(plg: 'AbstractPlugin', op: str):
			plugin_requirements.append(as_requirement(plg, op))
		plugin_requirements: List[PluginRequirement] = []

		try:
			input_requirements: List[PluginRequirement] = []
			for s in input_requirement_strings:
				if s != '*':
					input_requirements.append(PluginRequirement.of(s))
			if '*' in input_requirement_strings:
				for plugin in self.plugin_manager.get_regular_plugins():
					if isinstance(plugin, PackedPlugin):
						input_requirements.append(as_requirement(plugin, None))
			input_requirements = misc_util.unique_list(input_requirements)
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
					if do_update:
						add_requirement(plugin, '>=')
					else:
						add_requirement(plugin, '==')

		input_plugin_ids = {req.id for req in input_requirements}
		for plugin in self.plugin_manager.get_all_plugins():
			if plugin.get_id() not in input_plugin_ids:
				# pin for unselected plugins
				add_requirement(plugin, '==')

		self.log_debug('Generated plugin requirements:')
		for req in plugin_requirements:
			self.log_debug('{}'.format(req))

		# ------------------- Resolve -------------------

		source.reply('Resolving dependencies')

		cata_meta = self.get_cata_meta(source)
		plugin_resolver = PluginDependencyResolver(MergedMetaRegistry(cata_meta, LocalMetaRegistry(self.plugin_manager)))
		result = plugin_resolver.resolve(plugin_requirements)

		if isinstance(result, Exception):
			err = result
			if isinstance(err, resolvelib.ResolutionImpossible):
				source.reply('ResolutionImpossible!')
				for cause in err.causes:
					source.reply('    {} requires {}'.format(cause.parent, cause.requirement))
			else:
				source.reply('Resolution error: {}'.format(err))
			return

		resolution = result
		self.log_debug('Output plugin resolution:')
		for plugin_id, version in resolution.items():
			self.log_debug('{} {}'.format(plugin_id, version))

		class ToInstallData(NamedTuple):
			id: str
			version: Version
			old_version: Optional[str]
			release: ReleaseData

		# collect to_install
		to_install: Dict[str, ToInstallData] = {}
		package_requirements: List[str] = []
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			if plugin is not None:
				old_version = plugin.get_metadata().version
			else:
				old_version = None
			if old_version != version:
				if plugin is not None and not isinstance(plugin, PackedPlugin):
					source.reply('Existing plugin {} is {} and cannot be reinstalled. Only packed plugin is supported'.format(plugin_id, type(plugin).__name__))
					return
				try:
					release = cata_meta.plugins[plugin_id].releases[str(version)]
				except KeyError:
					raise AssertionError('unexpected to-install plugin {} version {}'.format(plugin_id, version))
				if isinstance(release, LocalReleaseData):
					self.logger.warning('Skipping unexpected chosen LocalReleaseData {}'.format(release))
					continue
				to_install[plugin_id] = ToInstallData(
					id=plugin_id,
					version=version,
					old_version=old_version,
					release=release,
				)
				package_requirements.extend(release.requirements)

		if len(to_install) == 0:
			source.reply('Nothing is needed to be installed')
			return

		add_cnt, change_cnt = 0, 0
		for data in to_install.values():
			if data.old_version is not None:
				change_cnt += 1
			else:
				add_cnt += 1

		source.reply('Plugins to install (new {}, change {}, total {})'.format(add_cnt, change_cnt, len(to_install)))
		for plugin_id, data in to_install.items():
			source.reply('  {} {} -> {}'.format(plugin_id, data.old_version, data.version))
		if len(package_requirements) > 0:
			source.reply('Python packages to install')
			for req in sorted(package_requirements):
				source.reply('  {}'.format(req))

		package_resolver = PackageRequirementResolver(package_requirements)
		try:
			output = package_resolver.check()
		except subprocess.CalledProcessError as e:
			source.reply('Python package dependencies resolution error')
			for line in e.stdout.splitlines():
				source.reply('    {}'.format(line))
			return
		else:
			for line in (output or '').splitlines():
				self.log_debug('pip output: {}'.format(line))

		# ------------------- Install -------------------
		dry_run_suffix = ' (dry-run)' if dry_run else ''
		if not skip_confirm:
			self.__installation_confirm_helper.clear()
			source.reply('Entry `!!MCDR confirm` to confirm installation, or `!!MCDR abort` to abort' + dry_run_suffix)

			self.__installation_source = source
			ok = self.__installation_confirm_helper.wait(self.CONFIRM_WAIT_TIMEOUT)
			self.__installation_source = None

			ich_state = self.__installation_confirm_helper.get()
			if ich_state == ConfirmHelperState.cancelled:
				return
			elif ich_state == ConfirmHelperState.aborted:
				source.reply('Plugin installation abort')
				return
			if not ok:
				source.reply('Plugin installation confirmation timed out')
				return

		# download
		download_temp_dir = Path(self.server_interface.get_data_folder()) / 'pim_{}'.format(os.getpid())  # todo: better dir name
		if not dry_run and download_temp_dir.is_dir():
			shutil.rmtree(download_temp_dir)
		downloaded_files: Dict[str, Path] = {}
		trashbin_path = download_temp_dir / '_trashbin'
		trashbin_files: Dict[Path, Path] = {}  # trashbin path -> origin path
		newly_added_files: List[Path] = []
		try:
			source.reply('Downloading {} plugins'.format(len(to_install)))
			for plugin_id, data in to_install.items():
				download_temp_file = download_temp_dir / '{}.tmp'.format(plugin_id)
				downloaded_files[plugin_id] = download_temp_file
				source.reply('Downloading {}@{}: {!r}'.format(plugin_id, data.version, data.release.file_name) + dry_run_suffix)
				if not dry_run:
					download_temp_file.parent.mkdir(parents=True, exist_ok=True)
					ReleaseDownloader(data.release, download_temp_file, CommandSourceReplier(source)).download()

			if len(package_requirements) > 0:
				source.reply('Installing required python packages'.format(len(to_install)))
				if dry_run:
					source.reply('Installed {}'.format(package_resolver.package_requirements) + dry_run_suffix)
				else:
					try:
						package_resolver.install()
					except subprocess.CalledProcessError as e:
						source.reply('Python package installation error: {}'.format(e))
						self.server_interface.logger.exception('Python package installation error', e)
						return

			# apply
			to_load_paths: List[str] = []
			to_unload_ids: List[str] = []
			for plugin_id, data in to_install.items():
				plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is not None:
					if not isinstance(plugin, PackedPlugin):
						raise AssertionError('to_install contains a non-packed plugin {!r}'.format(plugin))
					path = Path(plugin.plugin_path)
					target_dir = path.parent
					trash_path = trashbin_path / '{}.tmp'.format(plugin_id)
					if not dry_run:
						trashbin_files[trash_path] = path
						trash_path.parent.mkdir(parents=True, exist_ok=True)
						shutil.move(path, trash_path)
				else:
					target_dir = default_target_path

				file_name = sanitize_filename(data.release.file_name)
				src = downloaded_files[plugin_id]
				dst = target_dir / file_name
				if dst.is_file():
					for i in range(1000):
						parts = file_name.rsplit('.', 1)
						parts[0] += '_{}'.format(i + 1)
						dst = target_dir / '.'.join(parts)
				source.reply('Installing {}@{} to {}'.format(plugin_id, data.version, dst) + dry_run_suffix)
				if not dry_run:
					newly_added_files.append(dst)
					shutil.move(src, dst)

				to_load_paths.append(str(dst))
				if plugin is not None:
					to_unload_ids.append(plugin_id)

			# reload
			source.reply('Reloading MCDR' + dry_run_suffix)
			if not dry_run:
				self.server_interface.manipulate_plugins(unload=to_unload_ids, load=to_load_paths)
			source.reply('done')
		except Exception as e:
			self.logger.error('File operation error ({}), performing rollback'.format(e))
			try:
				for new_file in newly_added_files:
					self.logger.warning('(rollback) Deleting new file {}'.format(new_file))
					new_file.unlink(missing_ok=True)
				for trash_path, origin_path in trashbin_files.items():
					self.logger.warning('(rollback) Restoring old plugin {}'.format(origin_path))
					shutil.move(trash_path, origin_path)
			except Exception:
				self.logger.exception('Rollback failed')
			raise
		finally:
			if download_temp_dir.is_dir():
				shutil.rmtree(download_temp_dir)

