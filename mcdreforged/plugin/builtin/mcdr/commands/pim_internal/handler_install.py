import contextlib
import dataclasses
import os
import re
import shlex
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Dict

from typing_extensions import override

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.command_source import CommandSource
from mcdreforged.minecraft.rtext.style import RColor, RAction, RStyle
from mcdreforged.minecraft.rtext.text import RTextBase, RText
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal import pim_utils
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.abort_helper import AbortHelper
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.confirm_helper import ConfirmHelper, ConfirmHelperState
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.exceptions import OuterReturn
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_base import PimCommandHandlerBase
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.local_meta_registry import LocalReleaseData
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.plugin_requirement_source import PluginRequirementSource
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.texts import Texts
from mcdreforged.plugin.installer.dependency_resolver import PluginRequirement, PluginDependencyResolver, PackageRequirementResolver, PluginCandidate, PluginDependencyResolverArgs
from mcdreforged.plugin.installer.downloader import ReleaseDownloader
from mcdreforged.plugin.installer.types import ReleaseData, PluginResolution, MetaRegistry
from mcdreforged.plugin.meta.version import Version
from mcdreforged.utils import misc_utils
from mcdreforged.utils.replier import CommandSourceReplier

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.commands.plugin_command_pim import PluginCommandPimExtension
	from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommandEvent
	from mcdreforged.plugin.type.plugin import AbstractPlugin


def read_mcdr_plugin_requirement_file(file_path: Path) -> List[str]:
	reqs: List[str] = []
	with open(file_path, 'r', encoding='utf8') as f:
		for line in f:
			line = line.split('#', 1)[0].strip()
			if len(line) > 0:
				reqs.append(line)
	return reqs


def is_plugin_updatable(plg: 'AbstractPlugin') -> bool:
	"""i.e. plugin is a packed plugin"""
	from mcdreforged.plugin.type.packed_plugin import PackedPlugin
	return isinstance(plg, PackedPlugin)


def sanitize_filename(filename: str) -> str:
	return re.sub(r'[\\/*?"<>|:]', '_', filename.strip())


@dataclasses.dataclass(frozen=True)
class _ParsedContext:
	input_specifiers: List[str]
	default_install_dir: Path
	do_upgrade: bool
	dry_run: bool
	skip_confirm: bool
	no_deps: bool


@dataclasses.dataclass(frozen=True)
class _PluginToInstallData:
	id: str
	version: Version
	old_version: Optional[Version]
	release: ReleaseData


@dataclasses.dataclass(frozen=True)
class _ParsedPluginRequirements:
	requirement_sources: Dict[PluginRequirement, PluginRequirementSource] = dataclasses.field(default_factory=dict)
	hash_validators: Dict[str, str] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class _ToInstallStuffs:
	# python packages, package req -> candidate
	packages: Dict[str, PluginCandidate] = dataclasses.field(default_factory=dict)
	# mcdr plugins, plugin id -> data
	plugins: Dict[str, _PluginToInstallData] = dataclasses.field(default_factory=dict)


class PimInstallCommandHandler(PimCommandHandlerBase):
	def __init__(self, pim_ext: 'PluginCommandPimExtension'):
		super().__init__(pim_ext)
		self.__install_source: Optional[CommandSource] = None
		self.__install_confirm_helper = ConfirmHelper()
		self.__install_abort_helper = AbortHelper()

	@override
	def process(self, source: CommandSource, context: CommandContext):
		self.__install_source = source
		self.__install_confirm_helper.clear()
		self.__install_abort_helper.clear()
		try:
			self.__process(source, context)
		finally:
			self.__install_source = None

	# ------------------------------------------------
	#             Command Implementation
	# ------------------------------------------------

	def __check_abort(self, source: CommandSource):
		if self.__install_abort_helper.is_aborted():
			source.reply(self._tr('install.aborted'))
			raise OuterReturn()

	def __process(self, source: CommandSource, context: CommandContext):
		# 1. Process user input
		ctx = self.__step_parse_input(source, context)
		self.log_debug('pim install ctx: {}'.format(ctx))

		# 2. Verify and collect requirements
		ppr = self.__step_parse_plugin_requirements(source, ctx)

		# 3. Resolve what will be installed
		cata_meta = self.get_merged_cata_meta(source)
		resolution = self.__step_resolve(source, ctx, ppr, cata_meta)
		to_install = self.__step_collect_to_install(source, ctx, ppr, cata_meta, resolution)

		# 4. Install packages and plugins
		self.__step_install(source, ctx, cata_meta, to_install)

	def __step_parse_input(self, source: CommandSource, context: CommandContext) -> _ParsedContext:
		input_specifiers: List[str] = []
		if len(arg_specifiers := context.get('plugin_specifier', [])) > 0:
			input_specifiers.extend(arg_specifiers)
		if len(req_files := context.get('requirement', [])) > 0:
			for req_file in req_files:
				try:
					file_specifiers = read_mcdr_plugin_requirement_file(Path(req_file))
				except OSError as e:
					source.reply(self._tr('install.read_file_error', repr(req_file), e).set_color(RColor.red))
					raise OuterReturn()
				else:
					input_specifiers.extend(file_specifiers)
		if not input_specifiers:
			source.reply(self._tr('install.no_input').set_color(RColor.red))
			raise OuterReturn()

		plugin_directories = self.plugin_manager.plugin_directories.copy()
		if len(plugin_directories) == 0:
			source.reply(self._tr('install.no_plugin_directories').set_color(RColor.red))
			raise OuterReturn()

		target: Optional[str] = context.get('target')
		if target is None:
			self.log_debug('target argument not provided, using the first entry of plugin_directories as the default_install_dir')
			default_install_dir = plugin_directories[0]
		else:
			for d in plugin_directories:
				if d.samefile(target):
					break
			else:
				source.reply(self._tr('install.invalid_target', target))
				raise OuterReturn()
			default_install_dir = Path(target)

		return _ParsedContext(
			input_specifiers=input_specifiers,
			default_install_dir=default_install_dir,
			do_upgrade=context.get('upgrade', 0) > 0,
			dry_run=context.get('dry_run', 0) > 0,
			skip_confirm=context.get('skip_confirm', 0) > 0,
			no_deps=context.get('no_deps', 0) > 0,
		)

	def __step_parse_plugin_requirements(self, source: CommandSource, ctx: _ParsedContext) -> _ParsedPluginRequirements:
		ppr = _ParsedPluginRequirements()
		req_srcs = ppr.requirement_sources

		def add_plugin_requirement(req_: PluginRequirement, req_src_: PluginRequirementSource):
			req_srcs[req_] = req_src_

		def add_implicit_plugin_requirement(plg: 'AbstractPlugin', preferred_version: Optional[Version]):
			if is_plugin_updatable(plg):
				add_plugin_requirement(pim_utils.as_requirement(plg, '>=', preferred_version=preferred_version), PluginRequirementSource.existing)
			else:
				add_plugin_requirement(pim_utils.as_requirement(plg, '==', preferred_version=preferred_version), PluginRequirementSource.existing_pinned)

		input_requirements: List[PluginRequirement] = []
		for s in ctx.input_specifiers:
			if s != '*':
				parts = s.split('@', 1)
				if len(parts) == 2:
					req_str, h = parts[0], parts[1].lower()
				else:
					req_str, h = s, None
				try:
					req = PluginRequirement.of(req_str)
				except ValueError as e:
					source.reply(self._tr('install.parse_specifier_failed', repr(s), e))
					raise OuterReturn()
				if h is not None:
					if re.fullmatch(r'[0-9abcdef]{10,64}', h) is None:  # len(sha256_hash_hex) == 64
						source.reply(self._tr('install.hash_validator_invalid', repr(s)))
						raise OuterReturn()
					cris = req.requirement.criterions
					if len(cris) == 1 and cris[0].opt == '==':
						ppr.hash_validators[req.id] = h
					else:
						source.reply(self._tr('install.hash_validator_unexpected', repr(s)))
						raise OuterReturn()
				input_requirements.append(req)

		if '*' in ctx.input_specifiers:
			for plugin in self.plugin_manager.get_regular_plugins():
				if is_plugin_updatable(plugin):
					input_requirements.append(pim_utils.as_requirement(plugin, None))

		input_requirements = misc_utils.unique_list(input_requirements)
		input_plugin_ids = {req.id for req in input_requirements}
		for req in input_requirements:
			if (plugin := self.plugin_manager.get_plugin_from_id(req.id)) is None:
				add_plugin_requirement(req, PluginRequirementSource.user_input)
				continue

			if plugin.is_builtin():
				source.reply(self._tr('install.cannot_install_builtin', plugin.get_id()))
				raise OuterReturn()

			# update installed plugin only when necessary, if do_upgrade is not provided
			pv = None if ctx.do_upgrade else plugin.get_version()
			if req.requirement.has_criterion():
				add_plugin_requirement(PluginRequirement(req.id, req.requirement, preferred_version=pv), PluginRequirementSource.user_input)
			else:
				add_implicit_plugin_requirement(plugin, pv)

		for plugin in self.plugin_manager.get_all_plugins():
			if plugin.get_id() not in input_plugin_ids:
				# update installed plugin only when necessary
				add_implicit_plugin_requirement(plugin, plugin.get_version())

		self.log_debug('Generated plugin requirements:')
		for req, req_src in req_srcs.items():
			self.log_debug('  {} ({})'.format(req, req_src))

		return ppr

	def __step_resolve(self, source: CommandSource, ctx: _ParsedContext, ppr: _ParsedPluginRequirements, cata_meta: MetaRegistry) -> PluginResolution:
		req_srcs = ppr.requirement_sources
		source.reply(self._tr('install.resolving_dependencies', len(req_srcs)))

		for req in req_srcs.keys():
			plugin_id = req.id
			if plugin_id not in cata_meta.plugins:
				source.reply(self._tr('install.unknown_plugin_id', Texts.plugin_id(plugin_id)))
				raise OuterReturn()

		resolver = PluginDependencyResolver(cata_meta)
		result = resolver.resolve(
			req_srcs.keys(),
			args=PluginDependencyResolverArgs(ignore_dependencies=ctx.no_deps),
		)

		if isinstance(result, Exception):
			pim_utils.show_resolve_error(source, result, self._tr, self.plugin_manager, req_src_getter=req_srcs.get)
			raise OuterReturn()

		self.log_debug('Output plugin resolution:')
		for plugin_id, version in result.items():
			self.log_debug('  {} {}'.format(plugin_id, version))
		return result

	def __step_collect_to_install(self, source: CommandSource, ctx: _ParsedContext, ppr: _ParsedPluginRequirements, cata_meta: MetaRegistry, resolution: PluginResolution) -> _ToInstallStuffs:
		to_install = _ToInstallStuffs()

		from mcdreforged.plugin.type.packed_plugin import PackedPlugin
		for plugin_id, version in resolution.items():
			plugin = self.plugin_manager.get_plugin_from_id(plugin_id)
			expected_hash = ppr.hash_validators.get(plugin_id)
			if plugin is not None:
				old_version = plugin.get_version()
			else:
				old_version = None
			if old_version != version:
				if plugin is not None and not isinstance(plugin, PackedPlugin):
					plugin_type_text = self._tr('install.cannot_change_not_packed.plugin_types.' + plugin.get_type().name)
					source.reply(self._tr('install.cannot_change_not_packed', plugin_id, plugin_type_text))
					raise OuterReturn()
				try:
					release = cata_meta[plugin_id].releases[str(version)]
				except KeyError:
					raise AssertionError('unexpected to-install plugin {} version {}'.format(plugin_id, version))
				if isinstance(release, LocalReleaseData):
					self.logger.warning('Skipping unexpected chosen LocalReleaseData {}'.format(release))
					continue
				if expected_hash is not None and not release.file_sha256.startswith(expected_hash):
					source.reply(self._tr(
						'install.mismatched_hash.catalogue',
						Texts.candidate(plugin_id, version), expected_hash, release.file_sha256
					).set_color(RColor.red))
					raise OuterReturn()
				to_install.plugins[plugin_id] = _PluginToInstallData(
					id=plugin_id,
					version=version,
					old_version=old_version,
					release=release,
				)
				for req in release.requirements:
					if req.lstrip().startswith('mcdreforged'):
						self.log_debug('Skipping mcdreforged requirement in requirements of plugin {}'.format(plugin_id))
					else:
						to_install.packages[req] = PluginCandidate(plugin_id, version)
			else:
				if expected_hash is not None and isinstance(plugin, PackedPlugin):
					current_hash = plugin.get_file_hash()
					if current_hash is not None and not current_hash.startswith(expected_hash):
						source.reply(self._tr(
							'install.mismatched_hash.local',
							Texts.candidate(plugin_id, plugin.get_version()), expected_hash, current_hash
						).set_color(RColor.red))
						raise OuterReturn()

		if len(to_install.plugins) == 0:
			source.reply(self._tr('install.nothing_to_install'))
			raise OuterReturn()

		add_cnt, change_cnt = 0, 0
		for data in to_install.plugins.values():
			if data.old_version is not None:
				change_cnt += 1
			else:
				add_cnt += 1

		source.reply(RTextBase.format(
			'{} ({}):',
			self._tr('install.install_summary.plugin_title').set_styles(RStyle.bold),
			self._tr(
				'install.install_summary.plugin_count',
				new=Texts.number(add_cnt),
				change=Texts.number(change_cnt),
				total=Texts.number(len(to_install.plugins)),
			)
		))
		source.reply('')
		for plugin_id, data in to_install.plugins.items():
			source.reply(pim_utils.INDENT + self._tr(
				'install.install_summary.plugin_entry',
				self.browse_cmd(plugin_id),
				RText(data.old_version) if data.old_version else RText('N/A', RColor.dark_gray),
				Texts.diff_version(data.old_version, data.version) if data.old_version else Texts.version(data.version),
			))
		source.reply('')

		if ctx.no_deps:
			self.log_debug('Discarded {} python packages requirements since no_deps is on'.format(len(to_install.packages)))
			to_install.packages.clear()

		if len(to_install.packages) > 0:
			source.reply(RTextBase.format(
				'{} ({}):',
				self._tr('install.install_summary.python_title').set_styles(RStyle.bold),
				self._tr('install.install_summary.python_count', Texts.number(len(to_install.packages)))
			))
			source.reply('')
			for req in sorted(to_install.packages.keys()):
				source.reply(pim_utils.INDENT + self._tr(
					'install.install_summary.python_entry',
					RText(req, RColor.blue).c(RAction.open_url, f'https://pypi.org/project/{req}/'),
					Texts.candidate(to_install.packages[req]),
				))
			source.reply('')

		return to_install

	def __step_install(self, source: CommandSource, ctx: _ParsedContext, cata_meta: MetaRegistry, to_install: _ToInstallStuffs):
		dry_run_suffix = self._tr('install.dry_run_suffix') if ctx.dry_run else RText('')
		if not ctx.skip_confirm:
			self.__install_confirm_helper.clear()
			source.reply(self._tr('install.confirm_hint', cmd_confirm=Texts.cmd('!!MCDR confirm'), cmd_abort=Texts.cmd('!!MCDR abort')) + dry_run_suffix)

			ok = self.__install_confirm_helper.wait(pim_utils.CONFIRM_WAIT_TIMEOUT)

			ich_state = self.__install_confirm_helper.get()
			if ich_state == ConfirmHelperState.cancelled:
				return
			elif ich_state == ConfirmHelperState.aborted:
				source.reply(self._tr('install.aborted'))
				return
			if not ok:
				source.reply(self._tr('install.confirm_timeout'))
				return

		self.__check_abort(source)

		# download
		base_dir = Path(self.server_interface.get_data_folder())
		self.delete_remaining_download_temp(base_dir)

		download_temp_dir = base_dir / 'pim_{}'.format(os.getpid())
		self.log_debug('download_temp_dir: {}'.format(download_temp_dir))
		if not ctx.dry_run and download_temp_dir.is_dir():
			shutil.rmtree(download_temp_dir)

		downloaded_files: Dict[str, Path] = {}  # plugin id -> downloaded temp file path
		trashbin_path = download_temp_dir / '_trashbin'
		trashbin_files: Dict[Path, Path] = {}  # trashbin path -> origin path
		newly_added_files: List[Path] = []

		try:
			# XXX: verify python package feasibility with PackageRequirementResolver.check
			package_resolver = PackageRequirementResolver(list(to_install.packages.keys()))

			if len(to_install.packages) > 0:
				source.reply(self._tr('install.installing_package', Texts.number(len(to_install.packages))))
				if ctx.dry_run:
					source.reply(self._tr('install.install_package_dry_run', ', '.join(to_install.packages.keys())) + dry_run_suffix)
				else:
					def log_cmd(cmd: List[str]):
						self.log_debug('pip install cmd: {}'.format(cmd))

					try:
						with self.__install_abort_helper.add_abort_callback(package_resolver.abort):
							package_resolver.install(
								extra_args=shlex.split(self.mcdr_server.config.plugin_pip_install_extra_args or ''),
								pre_run_callback=log_cmd,
							)
					except subprocess.CalledProcessError as e:
						source.reply(self._tr('install.install_package_failed', e))
						if source.is_console:
							self.server_interface.logger.exception('Python package installation failed', e)
						raise OuterReturn()

			self.__check_abort(source)

			source.reply(self._tr('install.downloading_installing_plugin', len(to_install.plugins)))
			for plugin_id, data in to_install.plugins.items():
				download_temp_file = download_temp_dir / '{}.tmp'.format(plugin_id)
				downloaded_files[plugin_id] = download_temp_file
				source.reply(self._tr(
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
						with self.__install_abort_helper.add_abort_callback(downloader.abort):
							downloader.download(show_progress=ReleaseDownloader.ShowProgressPolicy.if_costly)
					self.__check_abort(source)

			self.__check_abort(source)

			# do the actual plugin files installation
			to_load_paths: List[Path] = []
			to_unload_ids: List[str] = []
			from mcdreforged.plugin.type.packed_plugin import PackedPlugin

			for plugin_id, data in to_install.plugins.items():
				plugin = self.plugin_manager.get_plugin_from_id(plugin_id)

				install_target_dir: Path  # the target dir to place the new plugin
				if plugin is not None:
					if not isinstance(plugin, PackedPlugin):
						raise AssertionError('to_install_stuffs.plugins contains a non-packed plugin {!r}'.format(plugin))
					path = Path(plugin.plugin_path)

					# For existing plugin, install to where the existing plugin is
					install_target_dir = path.parent
					trash_path = trashbin_path / '{}.tmp'.format(plugin_id)
					if not ctx.dry_run:
						trashbin_files[trash_path] = path
						trash_path.parent.mkdir(parents=True, exist_ok=True)
						shutil.move(path, trash_path)
				else:
					# For new plugins, follow the user's argument
					install_target_dir = ctx.default_install_dir

				file_name = sanitize_filename(data.release.file_name)
				src = downloaded_files[plugin_id]
				dst = install_target_dir / file_name
				if dst.is_file():
					for i in range(1000):
						parts = file_name.rsplit('.', 1)
						parts[0] += '_{}'.format(i + 1)
						dst = install_target_dir / '.'.join(parts)
						if not dst.is_file():
							break
					else:
						raise Exception('Too many files with name like {} at {}'.format(file_name, install_target_dir))

				source.reply(self._tr(
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

		except OuterReturn:
			raise

		except Exception as e:
			self.logger.error(self._tr('install.installation_error', e).set_color(RColor.red))
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
			source.reply(self._tr('install.reloading_plugins', len(to_install.plugins)) + dry_run_suffix)
			if not ctx.dry_run:
				self.server_interface.manipulate_plugins(unload=to_unload_ids, load=to_load_paths)
			source.reply(self._tr('install.installation_done').set_color(RColor.green))

		finally:
			if download_temp_dir.is_dir():
				shutil.rmtree(download_temp_dir)

	# ------------------------------------------------
	#               Interfaces for PIM
	# ------------------------------------------------

	def delete_remaining_download_temp(self, data_dir: Optional[Path] = None):
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

	def try_prepare_for_duplicated_input(self, source: CommandSource, op_thread: threading.Thread) -> bool:
		sis = self.__install_source
		if sis is not None and sis == source:
			# Another installation command when waiting for installation
			# Cancel the existing one and perform another installation
			self.__install_confirm_helper.set(ConfirmHelperState.cancelled)
			if op_thread is not None:
				op_thread.join(0.5)

				# if op_thread is blocked at confirm wait, then op_thread will exit soon
				if op_thread.is_alive():
					self.log_debug('cmd_install_plugins thread is still alive after join'.format(op_thread))
				else:
					return True
		return False

	def on_event(self, source: Optional[CommandSource], event: 'SubCommandEvent') -> bool:
		sis = self.__install_source
		confirm_helper = self.__install_confirm_helper
		abort_helper = self.__install_abort_helper
		is_confirm_waiting = sis is not None and confirm_helper.is_waiting()

		from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommandEvent
		if event == SubCommandEvent.confirm:
			if is_confirm_waiting and source == sis:
				confirm_helper.set(ConfirmHelperState.confirmed)
				return True
		elif event == SubCommandEvent.abort:
			if sis is not None and source is not None and source.get_permission_level() >= sis.get_permission_level():
				abort_helper.abort()
				if is_confirm_waiting:
					confirm_helper.set(ConfirmHelperState.aborted)
				return True

		return False

	def on_mcdr_stop(self):
		self.__install_confirm_helper.set(ConfirmHelperState.aborted)
		self.__install_abort_helper.abort()
