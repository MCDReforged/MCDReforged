from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.info import Info


class ConsoleHandler(ThreadExecutor):
	def should_keep_looping(self):
		return True

	def tick(self):
		try:
			text = input()
			parsed_result: Info
			try:
				parsed_result = self.mcdr_server.server_handler_manager.get_current_handler().parse_console_command(text)
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('console_handler.parse_fail', text))
			else:
				self.mcdr_server.logger.debug('Parsed text from {}:'.format(type(self).__name__))
				for line in parsed_result.format_text().splitlines():
					self.mcdr_server.logger.debug('    {}'.format(line))
				self.mcdr_server.reactor_manager.put_info(parsed_result)
		except (KeyboardInterrupt, EOFError, SystemExit, IOError) as e:
			self.mcdr_server.logger.critical('Critical exception caught in {}: {} {}'.format(type(self).__name__, type(e).__name__, e))
			self.mcdr_server.interrupt()
		except:
			self.mcdr_server.logger.exception(self.mcdr_server.tr('console_handler.error'))
