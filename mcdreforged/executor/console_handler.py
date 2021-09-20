import sys
from threading import RLock
from typing import TYPE_CHECKING, Optional, Iterable, Any

from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.completion import Completion, CompleteEvent, WordCompleter, ThreadedCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.layout import Dimension
# noinspection PyProtectedMember
from prompt_toolkit.layout.menus import MultiColumnCompletionMenuControl
from prompt_toolkit.layout.processors import Processor, TransformationInput, Transformation
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.patch_stdout import StdoutProxy
from prompt_toolkit.shortcuts import CompleteStyle

from mcdreforged.command.command_source import CommandSource
from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.info_reactor.info import Info
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
		if self.mcdr_server.config['advanced_console']:
			self.console_kit.start_kits()
		super().loop()

	def stop(self):
		super().stop()
		self.console_kit.stop_kits()

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
						self.mcdr_server.logger.debug('	{}'.format(line), no_check=True)
				self.mcdr_server.reactor_manager.put_info(parsed_result)
		except (KeyboardInterrupt, EOFError, SystemExit, IOError) as error:
			if self.mcdr_server.is_server_running():
				self.mcdr_server.logger.critical('Critical exception caught in {}: {} {}'.format(type(self).__name__, type(error).__name__, error))
				if not self.mcdr_server.interrupt():  # not first try
					self.mcdr_server.logger.error('Console thread stopped')
					self.stop()
		except:
			self.mcdr_server.logger.exception(self.mcdr_server.tr('console_handler.error'))


class MCDRPromptSession(PromptSession):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.has_complete_this_line = False

	def _get_default_buffer_control_height(self) -> Dimension:
		dim = super()._get_default_buffer_control_height()
		# When there's no complete this line, don't reverse space for the autocompletion menu
		if not self.has_complete_this_line and self.default_buffer.complete_state is None:
			dim = Dimension()
		return dim

	def get_complete_state_checker(self) -> Processor:
		class CompleteStateChecker(Processor):
			def apply_transformation(self, ti: TransformationInput) -> Transformation:
				if len(ti.document.text) == 0:
					session.has_complete_this_line = False
				if buff.complete_state is not None:
					session.has_complete_this_line = True
				return Transformation(fragments=ti.fragments)

		buff = self.default_buffer
		session = self
		return CompleteStateChecker()


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
		self.words = sorted(misc_util.unique_list([suggestion.command for suggestion in suggestions]))
		self.display_dict = dict([(suggestion.command, suggestion.suggest_input) for suggestion in suggestions])
		return super().get_completions(document, complete_event)


class CommandArgumentSuggester(Processor):
	def __init__(self, command_manager: 'CommandManager'):
		super().__init__()
		self.command_manager = command_manager

	def apply_transformation(self, ti: TransformationInput) -> Transformation:
		# last line and cursor at end
		if ti.lineno == ti.document.line_count - 1 and ti.document.is_cursor_at_the_end:
			buffer = ti.buffer_control.buffer
			if not buffer.suggestion:
				input_ = ti.document.text
				suggestions = self.command_manager.suggest_command(input_, ConsoleSuggestionCommandSource())
				if suggestions.complete_hint is not None:
					return Transformation(fragments=ti.fragments + [('class:auto-suggestion', suggestions.complete_hint)])
		return Transformation(fragments=ti.fragments)


class PromptToolkitWrapper:
	def __init__(self, console_handler: ConsoleHandler):
		self.console_handler = console_handler  # type: ConsoleHandler
		self.__tr = console_handler.mcdr_server.tr
		self.__logger = console_handler.mcdr_server.logger
		self.pt_enabled = False
		self.stdout_proxy = None  # type: Optional[StdoutProxy]
		self.prompt_session = None  # type: Optional[MCDRPromptSession]
		self.__real_stdout = None
		self.__real_stderr = None
		self.__promoting = RLock()  # more for a status check

	def start_kits(self):
		try:
			self.__tweak_kits()
			self.prompt_session = MCDRPromptSession()
			self.stdout_proxy = StdoutProxy(sleep_between_writes=0.01, raw=True)
		except:
			self.__logger.exception('Failed to enable advanced console, switch back to basic input')
		else:
			self.__real_stdout = sys.stdout
			self.__real_stderr = sys.stderr
			sys.stdout = self.stdout_proxy
			sys.stderr = self.stdout_proxy
			SyncStdoutStreamHandler.update_stdout()
			self.pt_enabled = True
			self.__logger.debug('Prompt Toolkits enabled')

	@staticmethod
	def __tweak_kits():
		# monkey patch to yeet the bell sound
		Vt100_Output.bell = lambda self_: None

		# monkey patch to set min_rows to 2
		# since with reserve_space_for_menu=3, 2 row of completion menu can be displayed
		def min_rows_is_2(*args, **kwargs):
			kwargs['min_rows'] = 2
			real_ctor(*args, **kwargs)

		# noinspection PyTypeChecker
		real_ctor = MultiColumnCompletionMenuControl.__init__
		MultiColumnCompletionMenuControl.__init__ = min_rows_is_2

	def stop_kits(self):
		if self.pt_enabled:
			self.pt_enabled = False
			self.__logger.info(self.__tr('console_handler.stopping_kits'))
			self.stdout_proxy.close()
			sys.stdout = self.__real_stdout
			sys.stderr = self.__real_stderr
			SyncStdoutStreamHandler.update_stdout()
			pt_app = get_app()
			if pt_app.is_running:
				try:
					pt_app.exit()
				except:
					self.__logger.exception('Fail to stop prompt toolkit app')
			with self.__promoting:
				# make sure in the console thread, prompt_session.prompt() ends
				pass

	def get_input(self) -> Optional[str]:
		if self.pt_enabled:
			assert self.console_handler.is_on_thread()
			command_manager = self.console_handler.mcdr_server.command_manager
			completer = ThreadedCompleter(CommandCompleter(command_manager))
			input_processors = [
				CommandArgumentSuggester(command_manager),
				self.prompt_session.get_complete_state_checker()
			]
			with self.__promoting:
				return self.prompt_session.prompt(
					'> ',
					completer=completer,
					complete_in_thread=True,
					complete_while_typing=True,
					complete_style=CompleteStyle.MULTI_COLUMN,
					reserve_space_for_menu=3,
					input_processors=input_processors
				)
		else:
			return input()
