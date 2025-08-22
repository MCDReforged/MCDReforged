import asyncio
import contextlib
import logging
import queue
import sys
import threading
import time
from threading import RLock, Lock
from typing import TYPE_CHECKING, Optional, Iterable, List, Sized

from prompt_toolkit import PromptSession
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import CompletionState, Buffer
from prompt_toolkit.completion import Completion, CompleteEvent, WordCompleter
from prompt_toolkit.document import Document
from prompt_toolkit.layout import Dimension
# noinspection PyProtectedMember
from prompt_toolkit.layout.menus import MultiColumnCompletionMenuControl
from prompt_toolkit.layout.processors import Processor, TransformationInput, Transformation
from prompt_toolkit.output.vt100 import Vt100_Output
from prompt_toolkit.patch_stdout import StdoutProxy
from prompt_toolkit.shortcuts import CompleteStyle
from typing_extensions import override

from mcdreforged.command.builder.nodes.basic import CommandSuggestions
from mcdreforged.command.command_source import ConsoleCommandSource
from mcdreforged.executor.background_thread_executor import BackgroundThreadExecutor
from mcdreforged.info_reactor.info import Info
from mcdreforged.logging.debug_option import DebugOption
from mcdreforged.logging.stream_handler import SyncStdoutStreamHandler
from mcdreforged.permission.permission_level import PermissionLevel
from mcdreforged.utils import collection_utils
from mcdreforged.utils.types.message import MessageText

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer
	from mcdreforged.command.command_manager import CommandManager


class ConsoleHandler(BackgroundThreadExecutor):
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		super().__init__(mcdr_server.logger)
		self.mcdr_server = mcdr_server
		self.__tr = mcdr_server.create_internal_translator('console_handler').tr
		self.console_kit = PromptToolkitWrapper(self)

	def get_tr(self):
		return self.__tr

	@override
	def loop(self):
		if self.mcdr_server.config.advanced_console:
			self.console_kit.start_kits()
		super().loop()

	@override
	def stop(self):
		super().stop()
		self.console_kit.stop_kits()

	@override
	def tick(self):
		try:
			inputs = self.console_kit.get_input()
			if not isinstance(inputs, list):
				raise IOError()
			for text in inputs:
				if not isinstance(text, str):
					raise IOError()
				try:
					info: Info = self.mcdr_server.server_handler_manager.get_current_handler().parse_console_command(text)
				except Exception:
					self.mcdr_server.logger.exception(self.__tr('parse_fail', text))
				else:
					if self.mcdr_server.logger.should_log_debug(DebugOption.HANDLER):
						self.mcdr_server.logger.mdebug('Parsed text from {}: {}'.format(type(self).__name__, info), no_check=True)
					self.mcdr_server.reactor_manager.put_info(info)
		except (KeyboardInterrupt, EOFError) as error:  # ctrl + c, ctrl + z
			if not self.mcdr_server.is_mcdr_about_to_exit():
				self.mcdr_server.logger.error('User interruption caught in {}: {} {}'.format(type(self).__name__, type(error).__name__, error))
				self.mcdr_server.interrupt()
		except Exception:
			self.mcdr_server.logger.exception(self.__tr('error'))


class ConsoleSuggestionCommandSource(ConsoleCommandSource):
	@override
	def get_permission_level(self) -> int:
		return PermissionLevel.CONSOLE_LEVEL

	@override
	def reply(self, message: MessageText, **kwargs) -> None:
		pass


class CachedSuggestionProvider:
	def __init__(self, command_manager: 'CommandManager'):
		self.__command_manager = command_manager
		self.__lock = Lock()
		self.__calc_lock = Lock()
		self.__cache_input: Optional[str] = None
		self.__cache_suggestion: Optional[CommandSuggestions] = None

	@property
	def mcdr_server(self) -> 'MCDReforgedServer':
		return self.__command_manager.mcdr_server

	def suggest(self, input_: str) -> CommandSuggestions:
		with self.__lock:
			if input_ == self.__cache_input:
				return self.__cache_suggestion
		acq = self.__calc_lock.acquire(blocking=False)
		if not acq:
			return CommandSuggestions()  # empty suggestion
		try:
			info = self.mcdr_server.server_handler_manager.get_current_handler().parse_console_command(input_)
			command_source = ConsoleSuggestionCommandSource(self.__command_manager.mcdr_server, info)
			# noinspection PyProtectedMember
			info._attach_and_finalize(self.mcdr_server, command_source=command_source)

			suggestion = self.__command_manager.suggest_command(input_, command_source)
			with self.__lock:
				self.__cache_input = input_
				self.__cache_suggestion = suggestion
			return self.__cache_suggestion
		finally:
			self.__calc_lock.release()


class CommandCompleter(WordCompleter):
	def __init__(self, suggester: CachedSuggestionProvider):
		super().__init__([], sentence=True)
		self.suggester = suggester

	@override
	def get_completions(self, document: Document, complete_event: CompleteEvent) -> Iterable[Completion]:
		input_ = document.current_line_before_cursor
		suggestions = self.suggester.suggest(input_)
		self.words = sorted(collection_utils.unique_list([suggestion.command for suggestion in suggestions]))
		self.display_dict = dict([(suggestion.command, suggestion.suggest_input) for suggestion in suggestions])
		return super().get_completions(document, complete_event)


class CommandArgumentSuggester(Processor):
	def __init__(self, suggester: CachedSuggestionProvider):
		super().__init__()
		self.suggester = suggester

	@override
	def apply_transformation(self, ti: TransformationInput) -> Transformation:
		# last line and cursor at end
		if ti.lineno == ti.document.line_count - 1 and ti.document.is_cursor_at_the_end:
			buffer = ti.buffer_control.buffer
			if not buffer.suggestion:
				input_ = ti.document.text
				suggestions = self.suggester.suggest(input_)
				if suggestions.complete_hint is not None:
					return Transformation(fragments=ti.fragments + [('class:auto-suggestion', suggestions.complete_hint)])
		return Transformation(fragments=ti.fragments)


class MCDRPromptSession(PromptSession):
	def __init__(self, console_handler: ConsoleHandler):
		self.__console_handler: ConsoleHandler = console_handler
		# noinspection PyArgumentEqualDefault
		super().__init__(
			complete_in_thread=True,  # this will do the ThreadedCompleter wrapping automatically
			complete_while_typing=True,
			complete_style=CompleteStyle.MULTI_COLUMN,
			reserve_space_for_menu=3
		)
		suggester = CachedSuggestionProvider(self.__console_handler.mcdr_server.command_manager)
		self.completer = CommandCompleter(suggester)
		self.input_processors = [
			CommandArgumentSuggester(suggester),
			self.__get_complete_state_checker()
		]
		self.has_complete_this_line = False

	@staticmethod
	def _has_completion_now(buffer: Buffer) -> bool:
		# Completion calculation might be happening right now in another thread, so make a reference copy first.
		complete_state: Optional[CompletionState] = buffer.complete_state
		# Similarly, in addition to checking if it's None, we should check its completions field as well
		return complete_state is not None and complete_state.completions

	@override
	def _get_default_buffer_control_height(self) -> Dimension:
		dim = super()._get_default_buffer_control_height()
		# When there's no complete this line, don't reverse space for the autocompletion menu
		if not self.has_complete_this_line and not self._has_completion_now(self.default_buffer):
			dim = Dimension()
		return dim

	def __get_complete_state_checker(self) -> Processor:
		class __CompleteStateChecker(Processor):
			@override
			def apply_transformation(self, ti: TransformationInput) -> Transformation:
				if len(ti.document.text) == 0:
					session.has_complete_this_line = False
				if session._has_completion_now(buff):
					session.has_complete_this_line = True
				return Transformation(fragments=ti.fragments)

		buff = self.default_buffer
		session = self
		return __CompleteStateChecker()


class MCDRStdoutProxy(StdoutProxy):
	def __init__(self, logger: logging.Logger):
		super().__init__(sleep_between_writes=0.01, raw=True)
		self.__logger = logger
		self.__sleep_duration = self.sleep_between_writes
		self._flush_queue.maxsize = 1000

	@override
	def _write_thread(self) -> None:
		try:
			self.__write_thread()
		except Exception:
			with contextlib.suppress(OSError):
				self.__logger.critical(f'MCDRStdoutProxy.__write_thread() error', exc_info=True)
			raise

	def __write_thread(self) -> None:
		"""
		Almost the same as :meth:`StdoutProxy._write_thread`. See line comments for modifications
		"""
		# noinspection PyProtectedMember
		from prompt_toolkit.patch_stdout import _Done
		done = False

		while not done:
			item = self._flush_queue.get()
			if isinstance(item, _Done):
				break
			if not item:
				continue

			text: List[str] = [item]
			for i in range(100 - 1):  # MCDR modification: take 100 items at max each round
				try:
					item = self._flush_queue.get_nowait()
				except queue.Empty:
					break
				else:
					if isinstance(item, _Done):
						done = True
					else:
						text.append(item)

			app_loop = self._get_app_loop()
			self._write_and_flush(app_loop, ''.join(text))
			if app_loop is not None:
				time.sleep(self.sleep_between_writes)

	@classmethod
	def __is_closed_event_loop(cls, e: RuntimeError) -> bool:
		# Reference: asyncio.base_events.BaseEventLoop._check_closed
		# `raise RuntimeError('Event loop is closed')`
		return type(e) is RuntimeError and str(e) == 'Event loop is closed'

	@override
	def _write_and_flush(self, loop: Optional[asyncio.AbstractEventLoop], text: str):
		"""
		make sure the event loop queue does not accumulate too much, in case stdout spams
		"""
		if threading.current_thread() != self._flush_thread:
			raise AssertionError('_write_and_flush called on unexpected thread {}'.format(threading.current_thread().name))

		self.sleep_between_writes = self.__sleep_duration
		ready_queue = getattr(loop, '_ready', None)  # asyncio.base_events.BaseEventLoop._ready
		if loop is not None and isinstance(ready_queue, Sized) and len(ready_queue) >= 2:
			event = threading.Event()
			try:
				loop.call_soon_threadsafe(event.set)
			except RuntimeError as e:
				if not self.__is_closed_event_loop(e):
					raise
			else:
				t = time.time()
				event.wait(timeout=3)
				elapsed = time.time() - t

				self.sleep_between_writes = max(0, self.__sleep_duration - elapsed)

		if loop is not None and loop.is_closed():
			loop = None
		try:
			super()._write_and_flush(loop, text)
		except RuntimeError as e:
			if not self.__is_closed_event_loop(e):
				raise


class PromptToolkitWrapper:
	def __init__(self, console_handler: ConsoleHandler):
		self.__console_handler: ConsoleHandler = console_handler
		self.__tr = console_handler.get_tr()
		self.__logger = console_handler.logger
		self.pt_enabled = False
		self.stdout_proxy: Optional[StdoutProxy] = None
		self.prompt_session: Optional[MCDRPromptSession] = None
		self.__real_stdout = None
		self.__real_stderr = None
		self.__promoting = RLock()  # more for a status check

	def start_kits(self):
		try:
			self.__tweak_kits()
			self.prompt_session = MCDRPromptSession(self.__console_handler)
			self.stdout_proxy = MCDRStdoutProxy(self.__logger)
		except Exception:
			self.__logger.exception('Failed to enable advanced console, switch back to basic input')
		else:
			self.__real_stdout = sys.stdout
			self.__real_stderr = sys.stderr
			sys.stdout = self.stdout_proxy
			sys.stderr = self.stdout_proxy
			# noinspection PyTypeChecker
			SyncStdoutStreamHandler.update_stdout(sys.stdout)
			self.pt_enabled = True
			self.__logger.debug('Prompt Toolkits enabled')

	@staticmethod
	def __tweak_kits():
		# monkey patch to yeet the bell sound
		def dummy_func(_self):
			pass
		Vt100_Output.bell = dummy_func

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
			self.__logger.info(self.__tr('stopping_kits'))
			self.stdout_proxy.close()
			sys.stdout = self.__real_stdout
			sys.stderr = self.__real_stderr
			SyncStdoutStreamHandler.update_stdout(sys.stdout)
			pt_app = get_app()
			if pt_app.is_running:
				try:
					pt_app.exit()
				except Exception:
					self.__logger.exception('Fail to stop prompt toolkit app')
			with self.__promoting:
				# make sure in the console thread, prompt_session.prompt() ends
				pass

	def get_input(self) -> List[str]:
		if self.pt_enabled:
			assert self.__console_handler.is_on_thread()
			with self.__promoting:
				# It's possible for prompt-toolkit to return a string wth multiple lines when pasting (#146)
				input_ = self.prompt_session.prompt('> ')
				if input_ is None:
					input_ = ''
				return input_.splitlines()
		else:
			# Cannot just use input()
			# See #47
			return [sys.stdin.readline().rstrip('\r\n')]
