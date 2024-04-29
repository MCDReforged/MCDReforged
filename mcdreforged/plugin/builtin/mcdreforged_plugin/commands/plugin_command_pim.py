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
from typing import Optional, List, TYPE_CHECKING, Dict

import resolvelib
from typing_extensions import override, deprecated

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants.core_constant import DEFAULT_LANGUAGE
from mcdreforged.minecraft.rtext.style import RColor, RAction, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText, RTextList
from mcdreforged.plugin.builtin.mcdreforged_plugin.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.installer.catalogue_access import PluginCatalogueAccess
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, PluginDependencyResolver, PackageRequirementResolver, PluginCandidate
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.meta_holder import PersistCatalogueMetaRegistryHolder
from mcdreforged.plugin.installer.types import MetaRegistry, PluginData, ReleaseData, MergedMetaRegistry
from mcdreforged.plugin.meta.version import VersionRequirement, Version
from mcdreforged.utils import misc_util
from mcdreforged.utils.replier import CommandSourceReplier

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdreforged_plugin.mcdreforged_plugin import MCDReforgedPlugin
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


def mkcmd(s: str) -> RTextBase:
	return RText(s, color=RColor.gray).c(RAction.suggest_command, s)


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

	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)
		self.__meta_holder = PersistCatalogueMetaRegistryHolder(
			self.mcdr_server,
			Path(self.server_interface.get_data_folder()) / 'catalogue_meta_cache.json.xz',
			meta_json_url=self.mcdr_server.config.catalogue_meta_url,
			meta_fetch_interval=self.mcdr_server.config.catalogue_meta_fetch_interval,
			meta_fetch_timeout=self.mcdr_server.config.catalogue_meta_fetch_timeout,
		)
		self.__installation_confirm_helper = ConfirmHelper()
		self.__installation_source: Optional[CommandSource] = None

	@override
	@deprecated('use get_command_child_nodes instead')
	def get_command_node(self) -> Literal:
		raise NotImplementedError('this is not a real subcommand')

	def get_command_child_nodes(self) -> List[Literal]:
		def install_node() -> Literal:
			def suggest_plugin_id():
				keys = set(self.__meta_holder.get_registry().plugins.keys())
				keys.add('*')  # so user can update all installed plugins
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
			node.then(CountingLiteral({'-u', '--upgrade'}, 'upgrade').redirects(node))
			node.then(CountingLiteral('--dry-run', 'dry_run').redirects(node))
			node.then(CountingLiteral({'-y', '--yes'}, 'skip_confirm').redirects(node))
			node.then(CountingLiteral('--no-deps', 'no_deps').redirects(node))  # TODO
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
		self.__meta_holder.terminate()
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

	def __get_cata_meta(self, source: CommandSource, ignore_ttl: bool = False) -> MetaRegistry:
		def start_fetch_callback(no_skip: bool):
			if no_skip:
				source.reply(self.tr('mcdr_command.pim.common.fetch_start'))
			nonlocal has_start_fetch
			has_start_fetch = has_start_fetch

		def done_callback(e: Optional[Exception]):
			if e is None:
				if has_start_fetch:
					source.reply(self.tr('mcdr_command.pim.common.fetch_done'))
			else:
				source.reply(self.tr('mcdr_command.pim.common.fetch_failed', e))

		has_start_fetch = False
		return self.__meta_holder.get_registry_blocked(ignore_ttl=ignore_ttl, start_callback=start_fetch_callback, done_callback=done_callback)

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
		source.reply(self.tr('mcdr_command.pim.common.duplicated_input', self.tr('mcdr_command.pim.{}.name'.format(op_key))))

	plugin_installer_guard = async_operation(op_holder=current_operation, skip_callback=__handle_duplicated_input, thread_name='PluginInstaller')

	@plugin_installer_guard('browse')
	def cmd_browse_catalogue(self, source: CommandSource, context: CommandContext):
		keyword = context.get('keyword')
		if keyword is not None:
			source.reply(self.tr('mcdr_command.pim.browse.listing_keyed', keyword))
		else:
			source.reply(self.tr('mcdr_command.pim.browse.listing'))

		PluginCatalogueAccess.list_plugin(
			meta=self.__get_cata_meta(source),
			replier=CommandSourceReplier(source),
			keyword=keyword,
			table_header=(
				self.tr('mcdr_command.pim.browse.title.id'),
				self.tr('mcdr_command.pim.browse.title.name'),
				self.tr('mcdr_command.pim.browse.title.version'),
				self.tr('mcdr_command.pim.browse.title.description'),
			),
		)

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
		cata_meta = self.__get_cata_meta(source)
		resolver = PluginDependencyResolver(MergedMetaRegistry(cata_meta, LocalMetaRegistry(self.plugin_manager)))
		resolution = resolver.resolve(plugin_requirements)
		if isinstance(resolution, Exception):
			source.reply(self.tr('mcdr_command.pim.check_update.dependency_resolution_failed', resolution).set_color(RColor.red))
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
			latest_version = cata_meta.plugins[plugin_id].latest_version_parsed if plugin_id in cata_meta.plugins else None
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
			source.reply(self.tr('mcdr_command.pim.check_update.no_update.{}'.format('given' if plugin_ids else 'all'), len(plugins)))
			return

		kinds = [
			(len(update_able_plugins), 'mcdr_command.pim.check_update.updatable.what'),
			(len(not_update_able_plugins), 'mcdr_command.pim.check_update.not_updatable.what'),
			(len(up_to_date_plugins), 'mcdr_command.pim.check_update.up_to_date.what'),
		]
		source.reply(self.tr(
			'mcdr_command.pim.check_update.found_summary',
			RTextBase.join(', ', [self.tr(k, RText(n, RColor.gold)) for n, k in kinds if n > 0])
		))

		def diff_version(base: Version, new: Version) -> RTextBase:
			s1, s2 = str(base), str(new)
			i = 0
			for i in range(min(len(s1), len(s2))):
				if s1[i] != s2[i]:
					break
			if i == 0:
				return RText(s2, RColor.gold)
			else:
				return RText(s2[:i]) + RText(s2[i:], RColor.dark_aqua)

		if len(update_able_plugins) > 0:
			source.reply(self.tr('mcdr_command.pim.check_update.updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in update_able_plugins:
				# xxx 0.1.0 -> 0.2.0
				# xxx 0.1.0 -> 0.2.0 (latest: 0.3.0)
				texts = RTextList(
					'  ',
					RText(entry.id),
					' ',
					RText(entry.current_version),
					RText(' -> ', RColor.gray),
					diff_version(entry.current_version, entry.update_version),
				)
				if entry.update_version != entry.latest_version:
					texts.append(
						' (',
						self.tr('mcdr_command.pim.check_update.latest', diff_version(entry.current_version, entry.latest_version)),
						')',
					)
				source.reply(texts)
			source.reply('')

		if len(not_update_able_plugins) > 0:
			source.reply(self.tr('mcdr_command.pim.check_update.not_updatable.title').set_styles(RStyle.bold))
			source.reply('')
			for entry in not_update_able_plugins:
				if entry.is_packed_plugin:
					reason = self.tr('mcdr_command.pim.check_update.not_updatable.reason.constraints_not_satisfied')
				else:
					reason = self.tr('mcdr_command.pim.check_update.not_updatable.reason.not_packed_plugin')
				# xxx 0.1.0 (latest 0.2.0) -- yyy reason
				source.reply(RTextList(
					'  ',
					RText(entry.id),
					' ',
					RText(entry.current_version),
					' (',
					self.tr('mcdr_command.pim.check_update.latest', diff_version(entry.current_version, entry.latest_version)),
					') -- ',
					reason,
				))
			source.reply('')

		if len(update_able_plugins) > 0:
			source.reply(self.tr('mcdr_command.pim.check_update.updatable.hint1', mkcmd('!!MCDR plugin install -U ' + next(iter(update_able_plugins)).id)))
			source.reply(self.tr('mcdr_command.pim.check_update.updatable.hint2', mkcmd('!!MCDR plugin install -U *')))

	@plugin_installer_guard('validate')
	def cmd_validate_constraints(self, source: CommandSource, context: CommandContext):
		plugin_requirements = list(map(
			functools.partial(as_requirement, op='=='),
			self.plugin_manager.get_all_plugins()
		))
		resolver = PluginDependencyResolver(LocalMetaRegistry(self.plugin_manager))
		ret = resolver.resolve(plugin_requirements)
		if isinstance(ret, Exception):
			# TODO: better display? tho technically it shouldn't happen
			source.reply(self.tr('mcdr_command.pim.validate.failed', ret))
		else:
			source.reply(self.tr('mcdr_command.pim.validate.success'))

	def cmd_freeze(self, source: CommandSource, context: CommandContext):
		if context.get('all', 0) > 0:
			plugins = self.plugin_manager.get_all_plugins()
			source.reply(self.tr('mcdr_command.pim.freeze.freezing_all', len(plugins)))
		else:
			plugins = self.plugin_manager.get_regular_plugins()
			source.reply(self.tr('mcdr_command.pim.freeze.freezing_installed', len(plugins)))

		for plugin in plugins:
			source.reply('{}=={}'.format(plugin.get_id(), plugin.get_version()))

	def cmd_refresh_meta(self, source: CommandSource, context: CommandContext):
		self.__get_cata_meta(source, ignore_ttl=True)

	@plugin_installer_guard('install')
	def cmd_install_plugins(self, source: CommandSource, context: CommandContext):
		# ------------------- Prepare -------------------
		input_requirement_strings: Optional[List[str]] = context.get('plugin_requirement')
		if not input_requirement_strings:
			source.reply(self.tr('mcdr_command.pim.install.no_input').set_color(RColor.red))
			return
		plugin_directories = self.plugin_manager.plugin_directories.copy()
		if len(plugin_directories) == 0:
			source.reply(self.tr('mcdr_command.pim.install.no_plugin_directories').set_color(RColor.red))
			return

		target: Optional[str] = context.get('target')
		if target is None:
			default_target_path = plugin_directories[0]
		else:
			default_target_path = Path(target)
			for d in plugin_directories:
				if d.samefile(default_target_path):
					break
			else:
				source.reply(self.tr('mcdr_command.pim.install.invalid_target', default_target_path))

		do_upgrade: bool = context.get('upgrade', 0) > 0
		dry_run = context.get('dry_run', 0) > 0
		skip_confirm = context.get('skip_confirm', 0) > 0

		# ------------------- Verify and Collect -------------------

		from mcdreforged.plugin.type.packed_plugin import PackedPlugin

		class RequirementSource(enum.Enum):
			user_input = enum.auto()
			existing = enum.auto()
			existing_pinned = enum.auto()

		def add_plugin_requirement(req_: PluginRequirement, req_src_: RequirementSource):
			plugin_requirements[req_] = req_src_

		def add_implicit_plugin_requirement(plg: 'AbstractPlugin', preferred_version: Optional[Version]):
			if is_plugin_updatable(plg):
				add_plugin_requirement(as_requirement(plg, '>=', preferred_version=preferred_version), RequirementSource.existing)
			else:
				add_plugin_requirement(as_requirement(plg, '==', preferred_version=preferred_version), RequirementSource.existing_pinned)

		plugin_requirements: Dict[PluginRequirement, RequirementSource] = {}

		input_requirements: List[PluginRequirement] = []
		for s in input_requirement_strings:
			if s != '*':
				try:
					input_requirements.append(PluginRequirement.of(s))
				except ValueError as e:
					source.reply(self.tr('mcdr_command.pim.install.parse_specifier_failed', repr(s), e))
					return
		if '*' in input_requirement_strings:
			for plugin in self.plugin_manager.get_regular_plugins():
				if is_plugin_updatable(plugin):
					input_requirements.append(as_requirement(plugin, None))

		input_requirements = misc_util.unique_list(input_requirements)
		input_plugin_ids = {req.id for req in input_requirements}
		for req in input_requirements:
			if (plugin := self.plugin_manager.get_plugin_from_id(req.id)) is None:
				add_plugin_requirement(req, RequirementSource.user_input)
				continue

			if plugin.is_permanent():
				source.reply(self.tr('mcdr_command.pim.install.cannot_install_permanent', plugin.get_id()))
				return

			# update installed plugin only when necessary, if do_upgrade is not provided
			pv = None if do_upgrade else plugin.get_version()
			if req.requirement.has_criterion():
				add_plugin_requirement(PluginRequirement(req.id, req.requirement, preferred_version=pv), RequirementSource.user_input)
			else:
				add_implicit_plugin_requirement(plugin, pv)

		for plugin in self.plugin_manager.get_all_plugins():
			if plugin.get_id() not in input_plugin_ids:
				# update installed plugin only when necessary
				add_implicit_plugin_requirement(plugin, plugin.get_version())

		self.log_debug('Generated plugin requirements:')
		for req in plugin_requirements:
			self.log_debug('{}'.format(req))

		# ------------------- Resolve -------------------

		cata_meta = self.__get_cata_meta(source)

		source.reply(self.tr('mcdr_command.pim.install.resolving_dependencies'))
		plugin_resolver = PluginDependencyResolver(MergedMetaRegistry(cata_meta, LocalMetaRegistry(self.plugin_manager)))
		result = plugin_resolver.resolve(plugin_requirements.keys())

		if isinstance(result, Exception):
			err = result
			if isinstance(err, resolvelib.ResolutionImpossible):
				source.reply(self.tr('mcdr_command.pim.install.resolution.impossible'))
				source.reply('')
				showed_causes = set()
				for cause in err.causes:
					if cause in showed_causes:
						continue
					showed_causes.add(cause)
					cause_req: PluginRequirement = cause.requirement
					req_src = plugin_requirements.get(cause_req)
					if cause.parent is not None or req_src is None:
						source.reply('  ' + self.tr('mcdr_command.pim.install.resolution.impossible_requirements', cause.parent, cause_req))
					else:
						args = ()
						if req_src == RequirementSource.user_input:
							args = (cause_req,)
						elif req_src in [RequirementSource.existing, RequirementSource.existing_pinned]:
							plugin = self.plugin_manager.get_plugin_from_id(cause_req.id)
							args = (plugin.get_id(), plugin.get_version())
						source.reply('  ' + self.tr('mcdr_command.pim.install.resolution.source_reason.' + req_src.name, *args))
				source.reply('')
			else:
				source.reply(self.tr('mcdr_command.pim.install.resolution.error', err))
			return

		resolution = result
		self.log_debug('Output plugin resolution:')
		for plugin_id, version in resolution.items():
			self.log_debug('{} {}'.format(plugin_id, version))

		@dataclasses.dataclass(frozen=True)
		class ToInstallData:
			id: str
			version: Version
			old_version: Optional[str]
			release: ReleaseData

		# collect to_install
		to_install: Dict[str, ToInstallData] = {}
		package_requirements: Dict[str, PluginCandidate] = {}   # req -> candidate
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			if plugin is not None:
				old_version = plugin.get_version()
			else:
				old_version = None
			if old_version != version:
				if plugin is not None and not isinstance(plugin, PackedPlugin):
					source.reply(self.tr('mcdr_command.pim.install.cannot_change_not_packed', plugin_id, type(plugin).__name__))
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
				for req in release.requirements:
					if req.lstrip().startswith('mcdreforged'):
						self.log_debug('Skipping mcdreforged requirement in requirements of plugin {}'.format(plugin_id))
					else:
						package_requirements[req] = PluginCandidate(plugin_id, version)

		if len(to_install) == 0:
			source.reply(self.tr('mcdr_command.pim.install.nothing_to_install'))
			return

		add_cnt, change_cnt = 0, 0
		for data in to_install.values():
			if data.old_version is not None:
				change_cnt += 1
			else:
				add_cnt += 1

		source.reply(self.tr('mcdr_command.pim.install.install_summary.plugin', new=add_cnt, change=change_cnt, total=len(to_install)))
		for plugin_id, data in to_install.items():
			source.reply('  {}: {} -> {}'.format(plugin_id, data.old_version or RText('N/A', RColor.dark_gray), data.version))
		if len(package_requirements) > 0:
			source.reply(self.tr('mcdr_command.pim.install.install_summary.python'))
			for req in sorted(package_requirements.keys()):
				source.reply('  ' + self.tr('mcdr_command.pim.install.install_summary.python_entry', req, package_requirements[req]))

		package_resolver = PackageRequirementResolver(list(package_requirements.keys()))
		# XXX: verify python package feasibility

		# ------------------- Install -------------------
		dry_run_suffix = self.tr('mcdr_command.pim.install.dry_run_suffix') if dry_run else RText('')
		if not skip_confirm:
			self.__installation_confirm_helper.clear()
			source.reply(self.tr('mcdr_command.pim.install.confirm_hint', cmd_confirm=mkcmd('!!MCDR confirm'), cmd_abort=mkcmd('!!MCDR abort')) + dry_run_suffix)

			self.__installation_source = source
			ok = self.__installation_confirm_helper.wait(self.CONFIRM_WAIT_TIMEOUT)
			self.__installation_source = None

			ich_state = self.__installation_confirm_helper.get()
			if ich_state == ConfirmHelperState.cancelled:
				return
			elif ich_state == ConfirmHelperState.aborted:
				source.reply(self.tr('mcdr_command.pim.install.confirm_aborted'))
				return
			if not ok:
				source.reply(self.tr('mcdr_command.pim.install.confirm_timeout'))
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
			if len(package_requirements) > 0:
				source.reply(self.tr('mcdr_command.pim.install.installing_package', len(to_install)))
				if dry_run:
					source.reply(self.tr('mcdr_command.pim.install.install_package_dry_run', ', '.join(package_resolver.package_requirements)) + dry_run_suffix)
				else:
					try:
						package_resolver.install()
					except subprocess.CalledProcessError as e:
						source.reply(self.tr('mcdr_command.pim.install.install_package_failed', e))
						if source.is_console:
							self.server_interface.logger.exception('Python package installation failed', e)
						return

			source.reply(self.tr('mcdr_command.pim.install.downloading_plugin', len(to_install)))
			for plugin_id, data in to_install.items():
				download_temp_file = download_temp_dir / '{}.tmp'.format(plugin_id)
				downloaded_files[plugin_id] = download_temp_file
				source.reply(self.tr(
					'mcdr_command.pim.install.downloading_plugin_one',
					id=plugin_id,
					version=data.version,
					name=data.release.file_name,
					hash=data.release.file_sha256,
				) + dry_run_suffix)
				if not dry_run:
					download_temp_file.parent.mkdir(parents=True, exist_ok=True)
					ReleaseDownloader(
						data.release, download_temp_file, CommandSourceReplier(source),
						download_url_override=self.mcdr_server.config.plugin_download_url,
						download_timeout=self.mcdr_server.config.plugin_download_timeout,
					).download()

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
				source.reply(self.tr(
					'mcdr_command.pim.install.installing_plugin_one',
					id=plugin_id,
					version=data.version,
					path=str(dst),
				) + dry_run_suffix)
				if not dry_run:
					newly_added_files.append(dst)
					shutil.move(src, dst)

				to_load_paths.append(str(dst))
				if plugin is not None:
					to_unload_ids.append(plugin_id)

		except Exception as e:
			self.logger.error(self.tr('mcdr_command.pim.install.installation_error', e).set_color(RColor.red))
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
			source.reply(self.tr('mcdr_command.pim.install.reloading_plugins', len(to_install)) + dry_run_suffix)
			if not dry_run:
				self.server_interface.manipulate_plugins(unload=to_unload_ids, load=to_load_paths)
			source.reply(self.tr('mcdr_command.pim.install.installation_done').set_color(RColor.green))

		finally:
			if download_temp_dir.is_dir():
				shutil.rmtree(download_temp_dir)

