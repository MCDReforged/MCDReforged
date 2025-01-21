import dataclasses
import functools
import logging
import os
import re
import threading
from pathlib import Path
from typing import Optional, List, TYPE_CHECKING, Iterable, Callable, Set

from typing_extensions import override, deprecated

from mcdreforged.command.builder.common import CommandContext
from mcdreforged.command.builder.nodes.arguments import Text, QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.mcdr_config import MCDReforgedConfig
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal import pim_utils
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.exceptions import OuterReturn
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_browse import PimBrowseCommandHandler
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_check_update import PimCheckUpdateCommandHandler
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_freeze import PimFreezeCommandHandler
from mcdreforged.plugin.builtin.mcdr.commands.pim_internal.handler_install import PimInstallCommandHandler
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand, SubCommandEvent
from mcdreforged.plugin.installer.meta_holder import PersistCatalogueMetaRegistryHolder
from mcdreforged.plugin.installer.types import MetaRegistry
from mcdreforged.translation.translator import Translator
from mcdreforged.utils import misc_utils

if TYPE_CHECKING:
	from mcdreforged.plugin.builtin.mcdr.mcdreforged_plugin import MCDReforgedPlugin
	from mcdreforged.plugin.plugin_manager import PluginManager


@dataclasses.dataclass
class OperationHolder:
	lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)
	thread: Optional[threading.Thread] = dataclasses.field(default=None)
	op_key: Optional[str] = dataclasses.field(default=None)


def async_operation(op_holder: OperationHolder, skip_callback: Callable, thread_name: str):
	def decorator(op_key: str):
		def func_transformer(func: Callable):
			@functools.wraps(func)
			def wrapped_func(*args, **kwargs):
				acquired = op_holder.lock.acquire(blocking=False)
				if acquired:
					def run():
						try:
							func(*args, **kwargs)
						except OuterReturn:
							pass
						finally:
							op_holder.thread = None
							op_holder.op_key = None
							op_holder.lock.release()
					try:
						thread = threading.Thread(target=run, name=thread_name)
						thread.start()
						op_holder.thread = thread
						op_holder.op_key = op_key
						return thread
					except BaseException:
						op_holder.lock.release()
						raise
				else:
					skip_callback(*args, op_func=wrapped_func, op_key=op_holder.op_key, op_thread=op_holder.thread, new_op_key=op_key, **kwargs)

			misc_utils.copy_signature(wrapped_func, func)
			return wrapped_func
		return func_transformer
	return decorator


class PluginCommandPimExtension(SubCommand):
	current_operation = OperationHolder()
	DEFAULT_FREEZE_FILE_NAME = 'mcdr_plugin_requirements.txt'

	def __init__(self, mcdr_plugin: 'MCDReforgedPlugin'):
		super().__init__(mcdr_plugin)
		self.__meta_holder = PersistCatalogueMetaRegistryHolder(
			self.mcdr_server,
			Path(self.server_interface.get_data_folder()) / 'catalogue_meta_cache.json.xz',
			meta_json_url=self.mcdr_server.config.catalogue_meta_url,
			meta_fetch_timeout=self.mcdr_server.config.catalogue_meta_fetch_timeout,
			meta_cache_ttl=self.mcdr_server.config.catalogue_meta_cache_ttl,
		)
		self.__tr = mcdr_plugin.get_translator().create_child('mcdr_command.pim')
		self.__browse_handler = PimBrowseCommandHandler(self)
		self.__check_update_handler = PimCheckUpdateCommandHandler(self)
		self.__install_handler = PimInstallCommandHandler(self)
		self.__freeze_handler = PimFreezeCommandHandler(self)

		self.mcdr_server.add_config_changed_callback(self.__on_mcdr_config_loaded)

	def __on_mcdr_config_loaded(self, config: MCDReforgedConfig, log: bool):
		# Notes: the builtin mcdreforged plugin is loaded after the initial config load,
		# so this callback will not be called in that initial config load
		self.__meta_holder.set_meta_json_url(config.catalogue_meta_url)
		self.__meta_holder.set_meta_fetch_timeout(config.catalogue_meta_fetch_timeout)
		self.__meta_holder.set_meta_cache_ttl(config.catalogue_meta_cache_ttl)
		self.log_debug('Updated pim meta_holder config to {}'.format({
			'meta_json_url': config.catalogue_meta_url,
			'meta_fetch_timeout': config.catalogue_meta_fetch_timeout,
			'meta_cache_ttl': config.catalogue_meta_cache_ttl,
		}))

	@property
	def pim_tr(self) -> Translator:
		return self.__tr

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
					suggests(lambda: self.__meta_holder.get_registry_fast().plugins.keys()).
					redirects(node)
				)
			)
			return node

		def install_node() -> Literal:
			plugin_id_prefix_regex = re.compile(r'^([a-z][a-z0-9_]+)')

			def suggest_plugin_id(_: CommandSource, ctx: CommandContext) -> Iterable[str]:
				input_str: Optional[str] = None
				input_plugin_id: Optional[str] = None
				if len(plugin_specifiers := ctx.get('plugin_specifier', [])) > 0:
					input_str = plugin_specifiers[-1]
					m = plugin_id_prefix_regex.search(input_str)
					if m is not None:
						input_plugin_id = m.group(1)

				suggestions: Set[str] = set()
				for plugin_id, plugin in self.__meta_holder.get_registry_fast().plugins.items():
					if input_str is None:
						suggestions.add(plugin_id)
					else:
						add_version_suggestions = False
						if input_str == plugin_id:
							suggestions.add(plugin_id)
							add_version_suggestions = True
						elif input_plugin_id == plugin_id:
							if input_str.startswith(f'{plugin_id}==') or f'{plugin_id}=='.startswith(input_str):
								add_version_suggestions = True
							else:  # user is input plugin_id + non '==' specifier
								pass
						elif plugin_id.startswith(input_str):
							suggestions.add(plugin_id)

						if add_version_suggestions:
							for version in plugin.releases.keys():
								suggestions.add(f'{plugin_id}=={version}')

				suggestions.add('*')  # so user can update all installed plugins
				return suggestions

			def suggest_target() -> Iterable[str]:
				return [str(path) for path in self.mcdr_server.plugin_manager.plugin_directories]

			node = Literal('install')
			node.runs(self.cmd_install_plugins)
			node.then(
				QuotableText('plugin_specifier', accumulate=True).
				suggests(suggest_plugin_id).
				redirects(node)
			)
			node.then(
				Literal({'-r', '--requirement'}).
				then(
					QuotableText('requirement_file', accumulate=True, metavar='requirement_file').
					suggests(lambda: [self.DEFAULT_FREEZE_FILE_NAME] if os.path.isfile(self.DEFAULT_FREEZE_FILE_NAME) else []).
					redirects(node)
				)
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

		def freeze_node() -> Literal:
			node = Literal('freeze')
			node.runs(self.cmd_freeze_installed_plugins)
			node.then(CountingLiteral({'-a', '--all'}, 'all').redirects(node))
			node.then(CountingLiteral('--no-hash', 'no_hash').redirects(node))
			node.then(
				Literal({'-o', '--output'}).
				then(QuotableText('output').suggests(lambda: [self.DEFAULT_FREEZE_FILE_NAME]).redirects(node))
			)
			return node

		return [
			browse_node(),
			check_update_node(),
			install_node(),
			refresh_meta_node(),
			freeze_node(),
		]

	@override
	def on_load(self):
		self.__meta_holder.init()
		self.__install_handler.delete_remaining_download_temp()

	@override
	def on_mcdr_stop(self):
		self.__meta_holder.terminate()
		self.__install_handler.on_mcdr_stop()
		thread = self.current_operation.thread
		if thread is not None:
			thread.join(timeout=pim_utils.CONFIRM_WAIT_TIMEOUT + 1)

	@override
	def on_event(self, source: Optional[CommandSource], event: SubCommandEvent) -> bool:
		is_handled = self.__install_handler.on_event(source, event)
		return is_handled

	@property
	def logger(self) -> logging.Logger:
		return self.server_interface.logger

	@property
	def plugin_manager(self) -> 'PluginManager':
		return self.mcdr_plugin.plugin_manager

	def get_cata_meta(self, source: CommandSource, ignore_ttl: bool) -> MetaRegistry:
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

	def __handle_duplicated_input(
			self, source: CommandSource, context: CommandContext,
			*,
			op_func: Callable, op_key: str, op_thread: Optional[threading.Thread], new_op_key: str,
	):
		if op_func == type(self).cmd_install_plugins:
			if self.__install_handler.try_prepare_for_duplicated_input(source, op_thread):
				self.cmd_install_plugins(source, context)
				return

		source.reply(self.__tr('common.duplicated_input', self.__tr('{}.name'.format(op_key))))

	plugin_installer_guard = async_operation(
		op_holder=current_operation,
		skip_callback=__handle_duplicated_input,
		thread_name='PIM',
	)

	@plugin_installer_guard('browse')
	def cmd_browse_catalogue(self, source: CommandSource, context: CommandContext):
		self.__browse_handler.process(source, context)

	@plugin_installer_guard('check_update')
	def cmd_check_update(self, source: CommandSource, context: CommandContext):
		self.__check_update_handler.process(source, context)

	@plugin_installer_guard('refreshmeta')
	def cmd_refresh_meta(self, source: CommandSource, _: CommandContext):
		self.get_cata_meta(source, ignore_ttl=True)

	@plugin_installer_guard('install')
	def cmd_install_plugins(self, source: CommandSource, context: CommandContext):
		self.__install_handler.process(source, context)

	def cmd_freeze_installed_plugins(self, source: CommandSource, context: CommandContext):
		self.__freeze_handler.process(source, context)
