import contextlib
import dataclasses
import enum
import functools
import logging
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Dict, Callable, Iterable

import resolvelib
from typing_extensions import override, deprecated

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor, RAction, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.pim_internal.abort_helper import AbortHelper
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.pim_internal.confirm_helper import ConfirmHelper, ConfirmHelperState
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.pim_internal.local_meta_registry import LocalMetaRegistry, LocalReleaseData
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.pim_internal.texts import Texts
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.installer.catalogue_access import PluginCatalogueAccess
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, PluginDependencyResolver, PackageRequirementResolver, PluginCandidate, PluginDependencyResolverArgs
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.meta_holder import PersistCatalogueMetaRegistryHolder
from mcdreforged.plugin.installer.types import MetaRegistry, ReleaseData, MergedMetaRegistry, PluginResolution
from mcdreforged.plugin.meta.version import VersionRequirement, Version
from mcdreforged.utils import misc_utils
from mcdreforged.utils.replier import CommandSourceReplier

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin
	from mcdreforged.plugin.plugin_manager import PluginManager
	from mcdreforged.plugin.type.plugin import AbstractPlugin


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


def is_plugin_updatable(plg: 'AbstractPlugin') -> bool:
	"""i.e. plugin is a packed plugin"""
	from mcdreforged.plugin.type.packed_plugin import PackedPlugin
	return isinstance(plg, PackedPlugin)


def sanitize_filename(filename: str) -> str:
	return re.sub(r'[\\/*?"<>|:]', '_', filename.strip())


@dataclasses.dataclass
class OperationHolder:
	lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)
	thread: threading.Thread = dataclasses.field(default=None)


class _OuterReturn(Exception):
	pass


def async_operation(op_holder: OperationHolder, skip_callback: callable, caller_func: callable, thread_name: str):
	def decorator(op_key: str):
		def func_transformer(func: callable):
			@functools.wraps(func)
			def wrapped_func(*args, **kwargs):
				acquired = op_holder.lock.acquire(blocking=False)
				if acquired:
					def run():
						try:
							caller_func(*args, func, **kwargs)
						except _OuterReturn:
							pass
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

			misc_utils.copy_signature(wrapped_func, func)
			return wrapped_func
		return func_transformer
	return decorator


class PluginCommandPimExtension(SubCommand):
	CONFIRM_WAIT_TIMEOUT = 60  # seconds
	INDENT = ' ' * 4
	current_operation = OperationHolder()

	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)
		self.__meta_holder = PersistCatalogueMetaRegistryHolder(
			self.mcdr_server,
			Path(self.server_interface.get_data_folder()) / 'catalogue_meta_cache.json.xz',
			meta_json_url=self.mcdr_server.config.catalogue_meta_url,
			meta_cache_ttl=self.mcdr_server.config.catalogue_meta_cache_ttl,
			meta_fetch_timeout=self.mcdr_server.config.catalogue_meta_fetch_timeout,
		)
		self.__installation_confirm_helper = ConfirmHelper()
		self.__installation_source: Optional[CommandSource] = None
		self.__installation_abort_helper = AbortHelper()
		self.__tr = mcdr_plugin.get_translator().create_child('mcdr_command.pim')

	@override
	@deprecated('use get_command_child_nodes instead')
	def get_command_node(self) -> Literal:
		raise NotImplementedError('this is not a real subcommand')

	def get_command_child_nodes(self) -> List[Literal]:
		def browse_node() -> Literal:
			node = Literal('browse')
			node.runs(self.cmd_browse_catalogue)
			node.then(QuotableText('keyword').runs(self.cmd_browse_catalogue))
			node.then(
				Literal({'-i', '--id'}).
				then(
					QuotableText('plugin_id').
					suggests(lambda: self.__meta_holder.get_registry().plugins.keys()).
					redirects(node)
				)
			)
			return node

		def install_node() -> Literal:
			def suggest_plugin_id() -> Iterable[str]:
				keys = set(self.__meta_holder.get_registry().plugins.keys())
				keys.add('*')  # so user can update all installed plugins
				return keys

			def suggest_target() -> Iterable[str]:
				return [str(path) for path in self.mcdr_server.plugin_manager.plugin_directories]

			node = Literal('install')
			node.runs(self.cmd_install_plugins)
			node.then(
				Text('plugin_specifier', accumulate=True).
				suggests(suggest_plugin_id).
				redirects(node)
			)
			node.then(
				Literal({'-t', '--target'}).
				then(
					QuotableText('target').
					suggests(suggest_target).
					redirects(node)
				)
			)
			node.then(CountingLiteral({'-u', '-U', '--upgrade'}, 'upgrade').redirects(node))
			node.then(CountingLiteral('--dry-run', 'dry_run').redirects(node))
			node.then(CountingLiteral({'-y', '--yes', '--confirm'}, 'skip_confirm').redirects(node))
			node.then(CountingLiteral('--no-dependencies', 'no_deps').redirects(node))
			return node

		def check_update_node() -> Literal:
			node = Literal({'checkupdate', 'cu'})
			node.runs(self.cmd_check_update)
			node.then(
				Text('plugin_id', accumulate=True).
				suggests(lambda: [plg.get_id() for plg in self.plugin_manager.get_regular_plugins()]).
				redirects(node)
			)
			return node

		def refresh_meta_node() -> Literal:
			node = Literal('refreshmeta')
			node.runs(self.cmd_refresh_meta)
			return node

		return [
			browse_node(),
			check_update_node(),
			install_node(),
			refresh_meta_node(),
		]

	@override
	def on_load(self):
		self.__meta_holder.init()
		self.__delete_remaining_download_temp()

	@override
	def on_mcdr_stop(self):
		self.__meta_holder.terminate()
		self.__installation_confirm_helper.set(ConfirmHelperState.aborted)
		self.__installation_abort_helper.abort()
		thread = self.current_operation.thread
		if thread is not None:
			thread.join(timeout=self.CONFIRM_WAIT_TIMEOUT + 1)

	@override
	def on_event(self, source: Optional[CommandSource], event: SubCommandEvent) -> bool:
		sis = self.__installation_source
		is_confirm_waiting = sis is not None and self.__installation_confirm_helper.is_waiting()
		if event == SubCommandEvent.confirm:
			if is_confirm_waiting and source == sis:
				self.__installation_confirm_helper.set(ConfirmHelperState.confirmed)
				return True
		elif event == SubCommandEvent.abort:
			if sis is not None and source is not None and source.get_permission_level() >= sis.get_permission_level():
				self.__installation_abort_helper.abort()
				if is_confirm_waiting:
					self.__installation_confirm_helper.set(ConfirmHelperState.aborted)
				return True
		return False

	@property
	def logger(self) -> logging.Logger:
		return self.server_interface.logger

	@property
	def plugin_manager(self) -> 'PluginManager':
		return self.mcdr_plugin.plugin_manager

	def __delete_remaining_download_temp(self, data_dir: Optional[Path] = None):
		if data_dir is None:
			data_dir = Path(self.server_interface.get_data_folder())
		for name in os.listdir(data_dir):
			dl_path = data_dir / name
			try:
				if dl_path.name.startswith('pim_') and dl_path.is_dir():
					if time.time() - dl_path.stat().st_mtime > 24 * 60 * 60:  # > 1day
						shutil.rmtree(dl_path)
						self.logger.info('Deleting old download temp dir {}'.format(dl_path))
			except OSError as e:
				self.logger.error('Error deleting renaming download temp dir {}: {}'.format(dl_path, e))

	def __get_cata_meta(self, source: CommandSource, ignore_ttl: bool = False) -> MetaRegistry:
		def start_fetch_callback(no_skip: bool):
			nonlocal has_start_fetch
			if has_start_fetch := no_skip:
				source.reply(self.__tr('common.fetch_start'))

		def done_callback(e: Optional[Exception]):
			if e is not None:
				source.reply(self.__tr('common.fetch_failed', e))
			elif has_start_fetch:
				source.reply(self.__tr('common.fetch_done'))

		def blocked_callback():
			source.reply(self.__tr('common.fetch_block_wait'))

		has_start_fetch = False
		return self.__meta_holder.get_registry_blocked(
			ignore_ttl=ignore_ttl,
			start_callback=start_fetch_callback,
			done_callback=done_callback,
			blocked_callback=blocked_callback,
		)

	def __handle_duplicated_input(self, source: CommandSource, context: CommandContext, op_func: callable, op_key: str, op_thread: Optional[threading.Thread]):
		if op_func == type(self).cmd_install_plugins:
			sis = self.__installation_source
			if sis is not None and sis == source:
				# Another installation command when waiting for installation
				# Cancel the existing one and perform another installation
				self.__installation_confirm_helper.set(ConfirmHelperState.cancelled)
				can_install = False
				if op_thread is not None:
					op_thread.join(0.5)

					# if op_thread is blocked at confirm wait, then op_thread will exit soon
					if op_thread.is_alive():
						self.log_debug('cmd_install_plugins thread is still alive after join'.format(op_thread))
					else:
						can_install = True
				if can_install:
					self.cmd_install_plugins(source, context)
					return

		source.reply(self.__tr('common.duplicated_input', self.__tr('{}.name'.format(op_key))))

	def __guard_wrapper(self, source: CommandSource, context: CommandContext, func: Callable):
		try:
			func(self, source, context)
		finally:
			self.__installation_source = None

	plugin_installer_guard = async_operation(
		op_holder=current_operation,
		skip_callback=__handle_duplicated_input,
		caller_func=__guard_wrapper,
		thread_name='PIM',
	)

	def __browse_cmd(self, plugin_id: str):
		return (
			Texts.plugin_id(plugin_id).
			h(self.__tr('common.browse_cmd', plugin_id)).
			c(RAction.run_command, '{} plugin browse --id {}'.format(self.control_command_prefix, plugin_id))
		)

	@plugin_installer_guard('browse')
	def cmd_browse_catalogue(self, source: CommandSource, context: CommandContext):
		cata_meta = self.__get_cata_meta(source)

		def browse_one():
			plugin_data = cata_meta.plugins.get(plugin_id)
			if plugin_data is None:
				source.reply('Plugin with id {} does not exist in the catalogue'.format(plugin_id))
				return

			na = RText('N/A', color=RColor.gray)
			source.reply(self.__tr('browse.single.id', Texts.plugin_id(plugin_data.id)))
			source.reply(self.__tr('browse.single.name', plugin_data.name or na))
			source.reply(self.__tr('browse.single.description', plugin_data.description_for(source.get_preference().language) or na))
			source.reply(self.__tr(
				'browse.single.repository',
				Texts.url(plugin_data.repos_pair, plugin_data.repos_url, underlined=False).
				h(self.__tr('browse.single.url', Texts.url(plugin_data.repos_url, plugin_data.repos_url)))
			))

			if len(plugin_data.releases) > 0 and plugin_data.latest_version is not None:
				def version_text(r: ReleaseData, anchor: bool) -> RTextBase:
					text = RTextList(
						Texts.version(r.version).
						c(RAction.suggest_command, '!!MCDR plugin install {}=={}'.format(plugin_id, r.version)).
						h(RTextBase.join('\n', [
							self.__tr('browse.single.version', Texts.version(r.version)),
							self.__tr('browse.single.date', r.created_at.strftime('%Y-%m-%d %H:%M:%S')),
						]))
					)
					if anchor:
						text.append(
							RText('*', color=RColor.blue).
							c(RAction.open_url, r.url).
							h(self.__tr('browse.single.url', Texts.url(r.url, r.url)))
						)
					return text

				latest = plugin_data.releases[plugin_data.latest_version]
				source.reply(self.__tr(
					'browse.single.latest_version',
					version_text(latest, False),
				))
				versions = []
				for release in plugin_data.releases.values():
					versions.append(version_text(release, True))

				source.reply(self.__tr('browse.single.releases', len(plugin_data.releases)))
				for i in range(0, len(versions), 10):
					line = RTextBase.join(', ', [versions[j] for j in range(i, min(i + 10, len(versions)))])
					source.reply(line)

		def browse_all():
			keyword = context.get('keyword')
			if keyword is not None:
				source.reply(self.__tr('browse.all.keyword', keyword))

			if source.is_player:
				# table does not display well in mc chat hud
				plugins = PluginCatalogueAccess.filter_sort(cata_meta.plugins.values(), keyword)
				for plg in plugins:
					source.reply(RTextList(
						self.__browse_cmd(plg.id).h(plg.name),
						RText(': ', RColor.gray),
						plg.description_for(source.get_preference().language)
					))
				if len(plugins) == 0:
					source.reply(self.__tr('browse.all.empty'))
			else:
				with source.preferred_language_context():  # required for table formatting
					cnt = PluginCatalogueAccess.list_plugin(
						meta=cata_meta,
						replier=CommandSourceReplier(source),
						keyword=keyword,
						table_header=(
							self.__tr('browse.all.title.id'),
							self.__tr('browse.all.title.name'),
							self.__tr('browse.all.title.version'),
							self.__tr('browse.all.title.description'),
						),
					)
				if cnt == 0:
					source.reply(self.__tr('browse.all.empty'))

		if (plugin_id := context.get('plugin_id')) is not None:
			browse_one()
		else:
			browse_all()

	class __PluginRequirementSource(enum.Enum):
		user_input = enum.auto()
		existing = enum.auto()
		existing_pinned = enum.auto()

	def __show_resolve_error(
			self, source: CommandSource, err: Exception, *,
			req_src_getter: Optional[Callable[[PluginRequirement], __PluginRequirementSource]] = None
	):
		if req_src_getter is None:
			req_src_getter = {}.get
		if isinstance(err, resolvelib.ResolutionImpossible):
			source.reply(self.__tr('install.resolution.impossible'))
			source.reply('')
			showed_causes = set()
			for cause in err.causes:
				if cause in showed_causes:
					continue
				showed_causes.add(cause)
				cause_req: PluginRequirement = cause.requirement
				req_src = req_src_getter(cause_req)
				if cause.parent is not None or req_src is None:
					source.reply(self.INDENT + self.__tr('install.resolution.impossible_requirements', cause.parent, cause_req))
				else:
					args = ()
					if req_src == self.__PluginRequirementSource.user_input:
						args = (cause_req,)
					elif req_src in [self.__PluginRequirementSource.existing, self.__PluginRequirementSource.existing_pinned]:
						plugin = self.plugin_manager.get_plugin_from_id(cause_req.id)
						args = (plugin.get_id(), plugin.get_version())
					source.reply(self.INDENT + self.__tr('install.resolution.source_reason.' + req_src.name, *args))
			source.reply('')
		else:
			source.reply(self.__tr('install.resolution.error', err))

	@plugin_installer_guard('check_update')
	def cmd_check_update(self, source: CommandSource, context: CommandContext):
		if len(plugin_ids := context.get('plugin_id', [])) > 0:
			for plugin_id in plugin_ids:
				plugin = self.mcdr_server.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is None:
					source.reply(super().tr('mcdr_command.invalid_plugin_id', plugin_id))
					return
			input_plugin_ids = set(plugin_ids)
		else:
			input_plugin_ids = {plugin.get_id() for plugin in self.plugin_manager.get_all_plugins()}

		plugin_requirements = []
		for plugin in self.plugin_manager.get_all_plugins():
			plugin_requirements.append(as_requirement(plugin, op='>=' if plugin.get_id() in input_plugin_ids else '=='))

		cata_meta = MergedMetaRegistry(self.__get_cata_meta(source), LocalMetaRegistry(self.plugin_manager))
		resolver = PluginDependencyResolver(cata_meta)
		resolution = resolver.resolve(plugin_requirements)
		if isinstance(resolution, Exception):
			def req_src_getter(req: PluginRequirement):
				if req.id in input_plugin_ids:
					return self.__PluginRequirementSource.existing
				else:
					return self.__PluginRequirementSource.existing_pinned

			source.reply(self.__tr('check_update.dependency_resolution_failed', resolution).set_color(RColor.red))
			self.__show_resolve_error(source, resolution, req_src_getter=req_src_getter)
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
			if plugin.is_permanent():
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
			source.reply(self.__tr('check_update.no_update.{}'.format('given' if plugin_ids else 'all'), len(input_plugin_ids)))
			return

		kinds = [
			(len(update_able_plugins), 'check_update.updatable.what'),
			(len(not_update_able_plugins), 'check_update.not_updatable.what'),
			(len(up_to_date_plugins), 'check_update.up_to_date.what'),
		]
		source.reply(self.__tr(
			'check_update.found_summary',
			RTextBase.join(', ', [self.__tr(k, Texts.number(n)) for n, k in kinds if n > 0])
		))

		if len(update_able_plugins) > 0:
			source.reply(self.__tr('check_update.updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in update_able_plugins:
				# xxx 0.1.0 -> 0.2.0
				# xxx 0.1.0 -> 0.2.0 (latest: 0.3.0)
				texts = RTextList(
					self.INDENT,
					self.__browse_cmd(entry.id),
					' ',
					RText(entry.current_version),
					RText(' -> ', RColor.gray),
					Texts.diff_version(entry.current_version, entry.update_version),
				)
				if entry.update_version != entry.latest_version:
					texts.append(
						' (',
						self.__tr('check_update.latest', Texts.diff_version(entry.current_version, entry.latest_version)),
						')',
					)
				source.reply(texts)
			source.reply('')

		if len(not_update_able_plugins) > 0:
			source.reply(self.__tr('check_update.not_updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in not_update_able_plugins:
				if entry.is_packed_plugin:
					reason = self.__tr('check_update.not_updatable.reason.constraints_not_satisfied')
				else:
					reason = self.__tr('check_update.not_updatable.reason.not_packed_plugin')
				# xxx 0.1.0 (latest 0.2.0) -- yyy reason
				source.reply(RTextList(
					self.INDENT,
					self.__browse_cmd(entry.id),
					' ',
					RText(entry.current_version),
					' (',
					self.__tr('check_update.latest', Texts.diff_version(entry.current_version, entry.latest_version)),
					') -- ',
					reason,
				))
			source.reply('')

		if len(update_able_plugins) > 0:
			source.reply(self.__tr('check_update.updatable.hint1', Texts.cmd('!!MCDR plugin install -U ' + next(iter(update_able_plugins)).id)))
			source.reply(self.__tr('check_update.updatable.hint2', Texts.cmd('!!MCDR plugin install -U *')))

	@plugin_installer_guard('refreshmeta')
	def cmd_refresh_meta(self, source: CommandSource, _: CommandContext):
		self.__get_cata_meta(source, ignore_ttl=True)

	@plugin_installer_guard('install')
	def cmd_install_plugins(self, source: CommandSource, context: CommandContext):
		# ------------------- Prepare -------------------
		input_specifiers: Optional[List[str]] = context.get('plugin_specifier')
		if not input_specifiers:
			source.reply(self.__tr('install.no_input').set_color(RColor.red))
			return

		def get_default_target_path() -> Path:
			plugin_directories = self.plugin_manager.plugin_directories.copy()
			if len(plugin_directories) == 0:
				source.reply(self.__tr('install.no_plugin_directories').set_color(RColor.red))
				raise _OuterReturn()

			target: Optional[str] = context.get('target')
			if target is None:
				return plugin_directories[0]
			else:
				for d in plugin_directories:
					if d.samefile(target):
						break
				else:
					source.reply(self.__tr('install.invalid_target', default_target_path))
					raise _OuterReturn()
				return Path(target)

		default_target_path = get_default_target_path()

		@dataclasses.dataclass
		class __Ctx:
			do_upgrade: bool = context.get('upgrade', 0) > 0
			dry_run = context.get('dry_run', 0) > 0
			skip_confirm = context.get('skip_confirm', 0) > 0
			no_deps = context.get('no_deps', 0) > 0

		ctx = __Ctx()
		self.log_debug('pim install ctx: {}'.format(ctx))

		def check_abort():
			if self.__installation_abort_helper.is_aborted():
				source.reply(self.__tr('install.aborted'))
				raise _OuterReturn()

		self.__installation_abort_helper.clear()
		self.__installation_source = source

		# ------------------- Verify and Collect -------------------

		def step_create_plugin_requirements():
			def add_plugin_requirement(req_: PluginRequirement, req_src_: PluginCommandPimExtension.__PluginRequirementSource):
				req_srcs[req_] = req_src_

			def add_implicit_plugin_requirement(plg: 'AbstractPlugin', preferred_version: Optional[Version]):
				if is_plugin_updatable(plg):
					add_plugin_requirement(as_requirement(plg, '>=', preferred_version=preferred_version), self.__PluginRequirementSource.existing)
				else:
					add_plugin_requirement(as_requirement(plg, '==', preferred_version=preferred_version), self.__PluginRequirementSource.existing_pinned)

			input_requirements: List[PluginRequirement] = []
			for s in input_specifiers:
				if s != '*':
					try:
						input_requirements.append(PluginRequirement.of(s))
					except ValueError as e:
						source.reply(self.__tr('install.parse_specifier_failed', repr(s), e))
						raise _OuterReturn()
			if '*' in input_specifiers:
				for plugin in self.plugin_manager.get_regular_plugins():
					if is_plugin_updatable(plugin):
						input_requirements.append(as_requirement(plugin, None))

			input_requirements = misc_utils.unique_list(input_requirements)
			input_plugin_ids = {req.id for req in input_requirements}
			for req in input_requirements:
				if (plugin := self.plugin_manager.get_plugin_from_id(req.id)) is None:
					add_plugin_requirement(req, self.__PluginRequirementSource.user_input)
					continue

				if plugin.is_permanent():
					source.reply(self.__tr('install.cannot_install_permanent', plugin.get_id()))
					raise _OuterReturn()

				# update installed plugin only when necessary, if do_upgrade is not provided
				pv = None if ctx.do_upgrade else plugin.get_version()
				if req.requirement.has_criterion():
					add_plugin_requirement(PluginRequirement(req.id, req.requirement, preferred_version=pv), self.__PluginRequirementSource.user_input)
				else:
					add_implicit_plugin_requirement(plugin, pv)

			for plugin in self.plugin_manager.get_all_plugins():
				if plugin.get_id() not in input_plugin_ids:
					# update installed plugin only when necessary
					add_implicit_plugin_requirement(plugin, plugin.get_version())

			self.log_debug('Generated plugin requirements:')
			for req, req_src in req_srcs.items():
				self.log_debug('{} ({})'.format(req, req_src))

		req_srcs: Dict[PluginRequirement, PluginCommandPimExtension.__PluginRequirementSource] = {}
		step_create_plugin_requirements()

		# ------------------- Resolve -------------------

		cata_meta = MergedMetaRegistry(self.__get_cata_meta(source), LocalMetaRegistry(self.plugin_manager))

		def step_resolve():
			source.reply(self.__tr('install.resolving_dependencies'))

			for req in req_srcs.keys():
				plugin_id = req.id
				if plugin_id not in cata_meta.plugins:
					source.reply(self.__tr('install.unknown_plugin_id', Texts.plugin_id(plugin_id)))
					raise _OuterReturn()

			resolver = PluginDependencyResolver(cata_meta)
			result = resolver.resolve(
				req_srcs.keys(),
				args=PluginDependencyResolverArgs(ignore_dependencies=ctx.no_deps),
			)

			if isinstance(result, Exception):
				self.__show_resolve_error(source, result, req_src_getter=req_srcs.get)
				raise _OuterReturn()

			self.log_debug('Output plugin resolution:')
			for plugin_id, version in result.items():
				self.log_debug('{} {}'.format(plugin_id, version))
			return result

		resolution: PluginResolution = step_resolve()

		@dataclasses.dataclass(frozen=True)
		class ToInstallData:
			id: str
			version: Version
			old_version: Optional[Version]
			release: ReleaseData

		def step_collect_to_install():
			from mcdreforged.plugin.type.packed_plugin import PackedPlugin
			for plugin_id, version in resolution.items():
				plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
				if plugin is not None:
					old_version = plugin.get_version()
				else:
					old_version = None
				if old_version != version:
					if plugin is not None and not isinstance(plugin, PackedPlugin):
						from mcdreforged.plugin.type.solo_plugin import SoloPlugin
						from mcdreforged.plugin.type.directory_plugin import DirectoryPlugin, LinkedDirectoryPlugin
						from mcdreforged.plugin.type.permanent_plugin import PermanentPlugin
						plugin_type_keys: Dict[type, str] = {
							PermanentPlugin: 'permanent_plugin',
							SoloPlugin: 'solo_plugin',
							PackedPlugin: 'packed_plugin',
							DirectoryPlugin: 'directory_plugin',
							LinkedDirectoryPlugin: 'lined_directory_plugin',
						}
						if (plugin_type_key := plugin_type_keys.get(type(plugin))) is not None:
							plugin_type_text = self.__tr('install.cannot_change_not_packed.plugin_types.' + plugin_type_key)
						else:
							plugin_type_text = RText(type(plugin).__name__)
						source.reply(self.__tr('install.cannot_change_not_packed', plugin_id, plugin_type_text))
						raise _OuterReturn()
					try:
						release = cata_meta[plugin_id].releases[str(version)]
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
					for req in release.requirements:
						if req.lstrip().startswith('mcdreforged'):
							self.log_debug('Skipping mcdreforged requirement in requirements of plugin {}'.format(plugin_id))
						else:
							package_requirements[req] = PluginCandidate(plugin_id, version)

			if len(to_install) == 0:
				source.reply(self.__tr('install.nothing_to_install'))
				raise _OuterReturn()

			add_cnt, change_cnt = 0, 0
			for data in to_install.values():
				if data.old_version is not None:
					change_cnt += 1
				else:
					add_cnt += 1

			source.reply(RTextBase.format(
				'{} ({}):',
				self.__tr('install.install_summary.plugin_title').set_styles(RStyle.bold),
				self.__tr(
					'install.install_summary.plugin_count',
					new=Texts.number(add_cnt),
					change=Texts.number(change_cnt),
					total=Texts.number(len(to_install)),
				)
			))
			source.reply('')
			for plugin_id, data in to_install.items():
				source.reply(self.INDENT + self.__tr(
					'install.install_summary.plugin_entry',
					self.__browse_cmd(plugin_id),
					RText(data.old_version) if data.old_version else RText('N/A', RColor.dark_gray),
					Texts.diff_version(data.old_version, data.version) if data.old_version else Texts.version(data.version),
				))
			source.reply('')

			if ctx.no_deps:
				self.log_debug('Discarded {} python packages requirements since no_deps is on'.format(len(package_requirements)))
				package_requirements.clear()

			if len(package_requirements) > 0:
				source.reply(RTextBase.format(
					'{} ({}):',
					self.__tr('install.install_summary.python_title').set_styles(RStyle.bold),
					self.__tr('install.install_summary.python_count', Texts.number(len(package_requirements)))
				))
				source.reply('')
				for req in sorted(package_requirements.keys()):
					source.reply(self.INDENT + self.__tr(
						'install.install_summary.python_entry',
						RText(req, RColor.blue).c(RAction.open_url, f'https://pypi.org/project/{req}/'),
						Texts.candidate(package_requirements[req]),
					))
				source.reply('')

		package_requirements: Dict[str, PluginCandidate] = {}   # package req -> candidate
		to_install: Dict[str, ToInstallData] = {}  # plugin id -> data
		step_collect_to_install()

		package_resolver = PackageRequirementResolver(list(package_requirements.keys()))
		# XXX: verify python package feasibility with PackageRequirementResolver.check

		# ------------------- Install -------------------

		def step_install():
			dry_run_suffix = self.__tr('install.dry_run_suffix') if ctx.dry_run else RText('')
			if not ctx.skip_confirm:
				self.__installation_confirm_helper.clear()
				source.reply(self.__tr('install.confirm_hint', cmd_confirm=Texts.cmd('!!MCDR confirm'), cmd_abort=Texts.cmd('!!MCDR abort')) + dry_run_suffix)

				ok = self.__installation_confirm_helper.wait(self.CONFIRM_WAIT_TIMEOUT)

				ich_state = self.__installation_confirm_helper.get()
				if ich_state == ConfirmHelperState.cancelled:
					return
				elif ich_state == ConfirmHelperState.aborted:
					source.reply(self.__tr('install.aborted'))
					return
				if not ok:
					source.reply(self.__tr('install.confirm_timeout'))
					return

			check_abort()

			# download
			base_dir = Path(self.server_interface.get_data_folder())
			self.__delete_remaining_download_temp(base_dir)

			download_temp_dir = base_dir / 'pim_{}'.format(os.getpid())
			self.log_debug('download_temp_dir: {}'.format(download_temp_dir))
			if not ctx.dry_run and download_temp_dir.is_dir():
				shutil.rmtree(download_temp_dir)

			downloaded_files: Dict[str, Path] = {}  # plugin id -> downloaded temp file path
			trashbin_path = download_temp_dir / '_trashbin'
			trashbin_files: Dict[Path, Path] = {}  # trashbin path -> origin path
			newly_added_files: List[Path] = []

			try:
				if len(package_requirements) > 0:
					source.reply(self.__tr('install.installing_package', Texts.number(len(package_requirements))))
					if ctx.dry_run:
						source.reply(self.__tr('install.install_package_dry_run', ', '.join(package_resolver.package_requirements)) + dry_run_suffix)
					else:
						def log_cmd(cmd: List[str]):
							self.log_debug('pip install cmd: {}'.format(cmd))
						try:
							with self.__installation_abort_helper.add_abort_callback(package_resolver.abort):
								package_resolver.install(
									extra_args=shlex.split(self.mcdr_server.config.plugin_pip_install_extra_args or ''),
									pre_run_callback=log_cmd,
								)
						except subprocess.CalledProcessError as e:
							source.reply(self.__tr('install.install_package_failed', e))
							if source.is_console:
								self.server_interface.logger.exception('Python package installation failed', e)
							raise _OuterReturn()

				check_abort()

				source.reply(self.__tr('install.downloading_installing_plugin', len(to_install)))
				for plugin_id, data in to_install.items():
					download_temp_file = download_temp_dir / '{}.tmp'.format(plugin_id)
					downloaded_files[plugin_id] = download_temp_file
					source.reply(self.__tr(
						'install.downloading_plugin_one',
						candidate=Texts.candidate(plugin_id, data.version),
						name=Texts.file_name(data.release.file_name),
						hash_quoted=RText(f'({data.release.file_sha256})', color=RColor.gray),
					) + dry_run_suffix)
					if not ctx.dry_run:
						download_temp_file.parent.mkdir(parents=True, exist_ok=True)
						downloader = ReleaseDownloader(
							data.release, download_temp_file, CommandSourceReplier(source),
							download_url_override=self.mcdr_server.config.plugin_download_url,
							download_url_override_kwargs={
								'repos_owner': cata_meta[plugin_id].repos_owner,
								'repos_name': cata_meta[plugin_id].repos_name,
							},
							download_timeout=self.mcdr_server.config.plugin_download_timeout,
							logger=self.logger,
						)
						with contextlib.suppress(downloader.Aborted):
							with self.__installation_abort_helper.add_abort_callback(downloader.abort):
								downloader.download(show_progress=ReleaseDownloader.ShowProgressPolicy.if_costly)
						check_abort()

				check_abort()

				# do the actual plugin files installation
				to_load_paths: List[Path] = []
				to_unload_ids: List[str] = []
				from mcdreforged.plugin.type.packed_plugin import PackedPlugin

				for plugin_id, data in to_install.items():
					plugin = self.plugin_manager.get_plugin_from_id(plugin_id)

					target_dir: Path  # the target dir to place the new plugin
					if plugin is not None:
						if not isinstance(plugin, PackedPlugin):
							raise AssertionError('to_install contains a non-packed plugin {!r}'.format(plugin))
						path = Path(plugin.plugin_path)

						# For existing plugin, install to where the existing plugin is
						target_dir = path.parent
						trash_path = trashbin_path / '{}.tmp'.format(plugin_id)
						if not ctx.dry_run:
							trashbin_files[trash_path] = path
							trash_path.parent.mkdir(parents=True, exist_ok=True)
							shutil.move(path, trash_path)
					else:
						# For new plugins, follow the user's argument
						target_dir = default_target_path

					file_name = sanitize_filename(data.release.file_name)
					src = downloaded_files[plugin_id]
					dst = target_dir / file_name
					if dst.is_file():
						for i in range(1000):
							parts = file_name.rsplit('.', 1)
							parts[0] += '_{}'.format(i + 1)
							dst = target_dir / '.'.join(parts)
							if not dst.is_file():
								break
						else:
							raise Exception('Too many files with name like {} at {}'.format(file_name, target_dir))

					source.reply(self.__tr(
						'install.installing_plugin_one',
						candidate=Texts.candidate(plugin_id, data.version),
						path=Texts.file_path(dst),
					) + dry_run_suffix)
					if not ctx.dry_run:
						newly_added_files.append(dst)
						shutil.move(src, dst)

					to_load_paths.append(dst)
					if plugin is not None:
						to_unload_ids.append(plugin_id)

			except _OuterReturn:
				raise

			except Exception as e:
				self.logger.error(self.__tr('install.installation_error', e).set_color(RColor.red))
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

			else:
				# download done, perform plugin reload
				source.reply(self.__tr('install.reloading_plugins', len(to_install)) + dry_run_suffix)
				if not ctx.dry_run:
					self.server_interface.manipulate_plugins(unload=to_unload_ids, load=to_load_paths)
				source.reply(self.__tr('install.installation_done').set_color(RColor.green))

			finally:
				if download_temp_dir.is_dir():
					shutil.rmtree(download_temp_dir)

		step_install()
