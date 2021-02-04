from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.info import Info
from mcdreforged.utils.logger import DebugOption


class ConsoleHandler(ThreadExecutor):
	def tick(self):
		try:
			text = input()
			parsed_result: Info
			try:
				parsed_result = self.mcdr_server.server_handler_manager.get_current_handler().parse_console_command(text)
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
