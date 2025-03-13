import functools
import json
import threading
from typing import List, Optional, Set, Dict, Generator, TypeVar

from typing_extensions import override

from mcdreforged.command.builder.nodes.arguments import QuotableText
from mcdreforged.command.builder.nodes.basic import Literal, AbstractNode
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.command.command_source import CommandSource
from mcdreforged.plugin.builtin.mcdr.commands.sub_command import SubCommand
from mcdreforged.plugin.plugin_registry import PluginCommandHolder
from mcdreforged.utils import thread_utils
from mcdreforged.utils.types.json_like import JsonLike
from mcdreforged.utils.types.message import TranslationStorage


def thread_dump(*, target_thread: Optional[str] = None, name_only: bool = False) -> List[str]:
	stack_map = thread_utils.get_stack_map().copy()
	lines: List[str] = []
	for thread in threading.enumerate():
		if target_thread is not None and thread.name != target_thread:
			continue
		tsi = thread_utils.get_stack_info(thread, stack_map=stack_map)
		if name_only:
			lines.append(tsi.head_line)
		else:
			lines.extend(tsi.get_lines())
	return lines


def json_wrap(obj: JsonLike) -> str:
	return json.dumps(obj, indent=4, ensure_ascii=False)


_AbstractNodeType = TypeVar('_AbstractNodeType', bound=AbstractNode)


class DebugCommand(SubCommand):
	@override
	def get_command_node(self) -> Literal:
		def with_output_file_argument(node: _AbstractNodeType, suggests: List[str]) -> _AbstractNodeType:
			return node.then(
				Literal({'-o', '--output'}).
				then(
					QuotableText('output_file').
					suggests(lambda: suggests).
					redirects(node)
				)
			)

		def translation_dump_suggest() -> Set[str]:
			result = {'.'}
			for k in self.translations.keys():
				parts = k.split('.')
				for i in range(len(parts)):
					result.add('.'.join(parts[:i + 1]))
			return result

		def suggest_thread_name() -> Generator[str, None, None]:
			yield '#all'
			for t in threading.enumerate():
				yield t.name

		def thread_dump_callback(src: CommandSource, ctx: dict):
			thread_name = ctx.get('thread_name')
			if thread_name == '#all':
				thread_name = None
			self.cmd_show_thread_dump(
				src,
				target_thread=thread_name,
				name_only=ctx.get('name_only', 0) > 0,
				output_file=ctx.get('output_file'),
			)

		def make_thread_dump_node() -> Literal:
			def decorate(n: _AbstractNodeType) -> _AbstractNodeType:
				n = with_output_file_argument(n, suggests=['mcdr_thread_dump.txt'])
				n.then(CountingLiteral('--name-only', 'name_only').redirects(n))
				return n
			node = decorate(Literal('thread_dump'))
			node.runs(thread_dump_callback)
			node.then(
				decorate(QuotableText('thread_name')).
				suggests(suggest_thread_name).
				runs(thread_dump_callback)
			)
			return node

		def make_translation_dump_node() -> Literal:
			wofa = functools.partial(with_output_file_argument, suggests=['mcdr_translation_dump.json'])
			node = Literal('translation')
			node.then(
				Literal('get').
				then(
					QuotableText('translation_key').
					suggests(lambda: self.translations.keys()).
					runs(lambda src, ctx: self.cmd_show_translation_entry(src, ctx['translation_key']))
				)
			)
			node.then(
				Literal('dump').
				then(
					wofa(QuotableText('json_path')).
					suggests(translation_dump_suggest).
					runs(lambda src, ctx: self.cmd_show_translation_dump(src, ctx['json_path'], output_file=ctx.get('output_file')))
				)
			)
			return node

		def make_command_dump_node() -> Literal:
			wofa = functools.partial(with_output_file_argument, suggests=['mcdr_command_dump.txt'])
			node = Literal('command_dump')
			node.then(
				wofa(Literal('all')).
				runs(lambda src, ctx: self.cmd_show_command_tree(src, show_all=True, output_file=ctx.get('output_file')))
			)
			node.then(
				Literal('plugin').
				then(
					wofa(QuotableText('plugin_id')).
					suggests(lambda: [plg.get_id() for plg in self.mcdr_server.plugin_manager.get_all_plugins()]).
					runs(lambda src, ctx: self.cmd_show_command_tree(src, plugin_id=ctx['plugin_id'], output_file=ctx.get('output_file')))
				)
			)
			node.then(
				Literal('node').
				then(
					wofa(QuotableText('literal_name')).
					suggests(lambda: self.command_roots.keys()).
					runs(lambda src, ctx: self.cmd_show_command_tree(src, literal_name=ctx['literal_name'], output_file=ctx.get('output_file')))
				)
			)
			return node

		return (
			self.owner_command_root('debug').
			runs(lambda src: self.reply_help_message(src, 'mcdr_command.help_message.debug')).
			then(make_thread_dump_node()).
			then(make_translation_dump_node()).
			then(make_command_dump_node())
		)

	@property
	def translations(self) -> TranslationStorage:
		return {**self.mcdr_server.plugin_manager.registry_storage.translations, **self.mcdr_server.translation_manager.translations}

	@property
	def command_roots(self) -> Dict[str, List[PluginCommandHolder]]:
		return self.mcdr_server.command_manager.root_nodes.copy()

	@classmethod
	def __write_file_or_reply(cls, source: CommandSource, lines: List[str], what: str, output_file: Optional[str]):
		if output_file is not None:
			try:
				with open(output_file, 'w', encoding='utf8') as f:
					for line in lines:
						f.write(line)
						f.write('\n')
			except OSError as e:
				source.reply('Error writing {} to file {!r}: {}'.format(what, output_file, e))
			else:
				source.reply('Written {} to file {!r}'.format(what, output_file))
		else:
			for line in lines:
				source.reply(line)

	@classmethod
	def cmd_show_thread_dump(cls, source: CommandSource, *, target_thread: Optional[str], name_only: bool, output_file: Optional[str] = None):
		lines = thread_dump(target_thread=target_thread, name_only=name_only)
		cls.__write_file_or_reply(source, lines, what='thread dump', output_file=output_file)

	def cmd_show_translation_entry(self, source: CommandSource, translation_key: str):
		entry = self.translations.get(translation_key.strip('.'))
		source.reply(json_wrap(entry))

	def cmd_show_translation_dump(self, source: CommandSource, json_path: str, *, output_file: Optional[str] = None):
		prefix_segments = list(filter(None, json_path.strip('.').split('.')))
		ret = {}
		for key, value in self.translations.items():
			key_segments = key.split('.')
			if key_segments[:len(prefix_segments)] == prefix_segments:
				ret[key] = value
		self.__write_file_or_reply(source, [json_wrap(ret)], what='translation dump', output_file=output_file)

	def cmd_show_command_tree(self, source: CommandSource, *, show_all: bool = False, plugin_id: Optional[str] = None, literal_name: Optional[str] = None, output_file: Optional[str] = None):
		roots: Dict[str, List[PluginCommandHolder]] = self.command_roots
		lines: List[str] = []
		for literal, holders in roots.items():
			if not show_all and (literal_name is not None and literal != literal_name):
				continue
			for holder in holders:
				if show_all or (plugin_id is None or holder.plugin.get_id() == plugin_id):
					holder.node.print_tree(lines.append)
		self.__write_file_or_reply(source, lines, what='command dump', output_file=output_file)
