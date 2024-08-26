import json
import platform
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import List, Optional, Set, Dict, TYPE_CHECKING

from typing_extensions import override

from mcdreforged.command.builder.nodes.arguments import QuotableText
from mcdreforged.command.builder.nodes.basic import Literal
from mcdreforged.command.command_source import CommandSource
from mcdreforged.constants import core_constant
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand
from mcdreforged.plugin.plugin_registry import PluginCommandHolder
from mcdreforged.utils.types.json_like import JsonLike
from mcdreforged.utils.types.message import TranslationStorage

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


def thread_dump(*, target_thread: Optional[str] = None) -> List[str]:
	# noinspection PyProtectedMember
	from sys import _current_frames
	lines = []
	stack_map = _current_frames().copy()
	for thread in threading.enumerate():
		thread_id, thread_name = thread.ident, thread.name
		if target_thread is not None and thread_name != target_thread:
			continue
		if thread_id in stack_map:
			lines.append("Thread {} (id {})".format(thread_name, thread_id))
			for filename, lineno, func_name, line in traceback.extract_stack(stack_map[thread_id]):
				lines.append('  File "{}", line {}, in {}'.format(filename, lineno, func_name))
				if line:
					lines.append('    {}'.format(line.strip()))
	return lines


def json_wrap(obj: JsonLike) -> str:
	return json.dumps(obj, indent=4, ensure_ascii=False)


class DebugCommand(SubCommand):
	@override
	def get_command_node(self) -> Literal:
		def translation_dump_suggest() -> Set[str]:
			result = {'.'}
			for k in self.translations.keys():
				parts = k.split('.')
				for i in range(len(parts)):
					result.add('.'.join(parts[:i + 1]))
			return result

		def suggest_thread_name():
			for t in threading.enumerate():
				yield t.name

		def thread_dump_callback(src: CommandSource, ctx: dict):
			self.cmd_show_thread_dump(src, ctx.get('thread_name'))

		return (
			self.owner_command_root('debug').
			runs(lambda src: self.reply_help_message(src, 'mcdr_command.help_message.debug')).
			then(
				Literal('thread_dump').
				runs(thread_dump_callback).
				then(
					Literal('#all').
					runs(thread_dump_callback)
				).
				then(
					QuotableText('thread_name').
					suggests(suggest_thread_name).
					runs(thread_dump_callback)
				)
			).
			then(
				Literal('translation').
				then(
					Literal('get').
					then(
						QuotableText('translation_key').
						suggests(lambda: self.translations.keys()).
						runs(lambda src, ctx: self.cmd_show_translation_entry(src, ctx['translation_key']))
					)
				).
				then(
					Literal('dump').
					then(
						QuotableText('json_path').
						suggests(translation_dump_suggest).
						runs(lambda src, ctx: self.cmd_show_translation_dump(src, ctx['json_path']))
					)
				)
			).
			then(
				Literal('command_dump').
				then(
					Literal('all').
					runs(lambda src: self.cmd_show_command_tree(src, show_all=True))
				).
				then(
					Literal('plugin').
					then(
						QuotableText('plugin_id').
						suggests(lambda: [plg.get_id() for plg in self.mcdr_server.plugin_manager.get_all_plugins()]).
						runs(lambda src, ctx: self.cmd_show_command_tree(src, plugin_id=ctx['plugin_id']))
					)
				).
				then(
					Literal('node').
					then(
						QuotableText('literal_name').
						suggests(lambda: self.command_roots.keys()).
						runs(lambda src, ctx: self.cmd_show_command_tree(src, literal_name=ctx['literal_name']))
					)
				)
			).
			then(
				Literal('dump').
				runs(self.cmd_debug_dump).
				then(
					Literal({'-o', '--output'}).
					then(QuotableText('output').runs(self.cmd_debug_dump))
				)
			)
		)

	@property
	def translations(self) -> TranslationStorage:
		return {**self.mcdr_server.plugin_manager.registry_storage.translations, **self.mcdr_server.translation_manager.translations}

	@property
	def command_roots(self) -> Dict[str, List[PluginCommandHolder]]:
		return self.mcdr_server.command_manager.root_nodes.copy()

	@classmethod
	def cmd_show_thread_dump(cls, source: CommandSource, target_thread: Optional[str]):
		for line in thread_dump(target_thread=target_thread):
			source.reply(line)

	def cmd_show_translation_entry(self, source: CommandSource, translation_key: str):
		entry = self.translations.get(translation_key.strip('.'))
		source.reply(json_wrap(entry))

	def cmd_show_translation_dump(self, source: CommandSource, json_path: str):
		prefix_segments = list(filter(None, json_path.strip('.').split('.')))
		ret = {}
		for key, value in self.translations.items():
			key_segments = key.split('.')
			if key_segments[:len(prefix_segments)] == prefix_segments:
				ret[key] = value
		source.reply(json_wrap(ret))

	def cmd_show_command_tree(self, source: CommandSource, *, show_all: bool = False, plugin_id: Optional[str] = None, literal_name: Optional[str] = None):
		roots: Dict[str, List[PluginCommandHolder]] = self.command_roots
		for literal, holders in roots.items():
			if not show_all and (literal_name is not None and literal != literal_name):
				continue
			for holder in holders:
				if show_all or (plugin_id is None or holder.plugin.get_id() == plugin_id):
					holder.node.print_tree(source.reply)

	def cmd_debug_dump(self, source: CommandSource, context: dict):
		full: bool = context.get('full', False)
		if (output := context.get('output')) is not None:
			output_path = Path(output)
		else:
			output_path = Path('.') / 'mcdreforged-dump-{}.json'.format(time.strftime('%Y%m%d-%H%M%S', time.localtime()))

		try:
			data = self.__create_debug_dump_dict(self.mcdr_server, full=full)
		except Exception:
			self.server_interface.logger.exception('Create debug dump dict failed')
			source.reply('')
			return

		with open(output_path, 'w', encoding='utf8') as f:
			json.dump(data, f, indent=2, ensure_ascii=False)
		source.reply('Created mcdreforged dump at {!r}'.format(str(output_path)))

	@classmethod
	def __create_debug_dump_dict(cls, mcdr_server: 'MCDReforgedServer', full: bool) -> dict:
		def dict_if_full(d: dict) -> dict:
			return d if full else {}

		# noinspection PyDictCreation
		data = {}

		data['version'] = {
			'name': core_constant.NAME,
			'version': core_constant.VERSION,
			'version_pypi': core_constant.VERSION_PYPI,
		}

		data['platform'] = {
			'python': sys.version,
			'python_version': platform.python_version(),
			'python_implementation': platform.python_implementation(),
			'python_compiler': platform.python_compiler(),
			'python_buildno': platform.python_build()[0],
			'python_builddate': platform.python_build()[1],
			'system': platform.platform(),
			'system_type': platform.system(),
			'system_release': platform.release(),
			'system_version': platform.version(),
			'system_architecture': platform.machine(),
		}

		data['config'] = mcdr_server.config.serialize()

		from mcdreforged.plugin.type.regular_plugin import RegularPlugin
		from mcdreforged.plugin.type.directory_plugin import LinkedDirectoryPlugin
		plugin_dump_list: List[dict] = []
		for plugin in mcdr_server.plugin_manager.get_all_plugins():
			plugin_dump = {
				'id': plugin.get_id(),
				'type': plugin.get_type().name.lower(),
				'state': plugin.state.name.lower(),
			}
			if isinstance(plugin, RegularPlugin):
				plugin_dump.update(dict_if_full({
					'file_path': str(plugin.file_path),
					'file_mtime': plugin.file_modify_time
				}))
			if isinstance(plugin, LinkedDirectoryPlugin):
				plugin_dump.update(dict_if_full({
					'target_plugin_path': str(plugin.target_plugin_path),
				}))
			plugin_dump.update({
				'metadata': plugin.get_metadata().to_dict(),
			})
			plugin_dump_list.append(plugin_dump)

		data['plugins'] = {
			'amount': len(mcdr_server.plugin_manager.get_all_plugins()),
			'plugins': plugin_dump_list,
		}

		from importlib.metadata import distributions
		data['package'] = {
			**dict_if_full({'sys_path': sys.path.copy()}),
			'packages': sorted([f'{dist.metadata["Name"]}=={dist.version}' for dist in distributions()]),
		}

		return data
