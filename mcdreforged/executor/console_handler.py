import sys
from typing import TYPE_CHECKING, Optional, Iterable, Any, Callable

from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completion, CompleteEvent, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import StyleAndTextTuples
from prompt_toolkit.lexers import Lexer
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.patch_stdout import StdoutProxy
from prompt_toolkit.shortcuts import CompleteStyle

from mcdreforged.command.command_source import CommandSource
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.info import Info
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.plugin.server_interface import ServerInterface
from mcdreforged.utils import misc_util
from mcdreforged.utils.logger import DebugOption, SyncStdoutStreamHandler

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.command.command_manager import CommandManager


class ConsoleHandler(ThreadExecutor):
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server)
		self.console_kit = PromptToolkitWrapper(self)

	def loop(self):
		if self.mcdr_server.config['advance_console']:
			self.console_kit.start_kits()
		super().loop()

	def tick(self):
		try:
			text = self.console_kit.get_input()
			if not isinstance(text, str):
				raise IOError()
			try:
				parsed_result: Info = self.mcdr_server.server_handler_manager.get_current_handler().parse_console_command(text)
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('console_handler.parse_fail', text))
			else:
				if self.mcdr_server.logger.should_log_debug(DebugOption.HANDLER):
					self.mcdr_server.logger.debug('Parsed text from {}:'.format(type(self).__name__), no_check=True)
					for line in parsed_result.format_text().splitlines():
						self.mcdr_server.logger.debug('    {}'.format(line), no_check=True)
				self.mcdr_server.reactor_manager.put_info(parsed_result)
		except (KeyboardInterrupt, EOFError, SystemExit, IOError) as error:
			if self.mcdr_server.is_server_running():
				self.mcdr_server.logger.critical('Critical exception caught in {}: {} {}'.format(type(self).__name__, type(error).__name__, error))
				self.mcdr_server.interrupt()
		except:
			self.mcdr_server.logger.exception(self.mcdr_server.tr('console_handler.error'))


class ConsoleSuggestionCommandSource(CommandSource):
	@property
	def is_player(self) -> bool:
		return False

	@property
	def is_console(self) -> bool:
		return True

	def get_server(self) -> 'ServerInterface':
		return ServerInterface.get_instance()

	def get_permission_level(self) -> int:
		return PermissionLevel.CONSOLE_LEVEL

	def reply(self, message: Any, **kwargs) -> None:
		pass


class CommandCompleter(WordCompleter):
	def __init__(self, command_manager: 'CommandManager'):
		super().__init__([], sentence=True)
		self.command_manager = command_manager

	def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
		input_ = document.current_line_before_cursor
		suggestions = self.command_manager.suggest_command(input_, ConsoleSuggestionCommandSource())
		self.words = misc_util.unique_list([suggestion.command for suggestion in suggestions])
		self.display_dict = dict([(suggestion.command, suggestion.suggest_input) for suggestion in suggestions])
		return super().get_completions(document, complete_event)


class PromptToolkitWrapper:
	def __init__(self, console_handler: ConsoleHandler):
		self.console_handler = console_handler  # type: ConsoleHandler
		self.enabled = False
		self.stdout_proxy = None  # type: Optional[StdoutProxy]
		self.prompt_session = None  # type: Optional[PromptSession]
		self.__real_stdout = None

	def start_kits(self):
		try:
			self.prompt_session = PromptSession()
			self.stdout_proxy = StdoutProxy(raw=True)
		except:
			pass
		else:
			self.__real_stdout = sys.stdout
			sys.stdout = self.stdout_proxy
			SyncStdoutStreamHandler.update_stdout()
			Vt100_Output.bell = lambda self_: None  # monkey patch to yeet the bell sound
			self.enabled = True

	def stop_kits(self):
		if self.enabled:
			self.stdout_proxy.close()
			sys.stdout = self.__real_stdout
			SyncStdoutStreamHandler.update_stdout()
			get_app().exit()

	def get_input(self) -> Optional[str]:
		if self.enabled:
			assert self.console_handler.is_on_thread()
			return self.prompt_session.prompt(
				'> ',
				completer=CommandCompleter(self.console_handler.mcdr_server.command_manager),
				enable_history_search=True,
				auto_suggest=AutoSuggestFromHistory(),
				complete_style=CompleteStyle.MULTI_COLUMN,
				reserve_space_for_menu=3
			)
		else:
			return input()


class MyLexer(Lexer):
	def lex_document(self, document: Document) -> Callable[[int], StyleAndTextTuples]:
		pass
