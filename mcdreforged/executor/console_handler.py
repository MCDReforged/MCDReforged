from mcdreforged.executor.thread_executor import ThreadExecutor
from mcdreforged.info import Info


class ConsoleHandler(ThreadExecutor):
	def should_keep_looping(self):
		return True

	def tick(self):
		# TODO: fix translation
		try:
			text = input()
			parsed_result: Info
			try:
				parsed_result = self.mcdr_server.parser_manager.get_parser().parse_console_command(text)
			except:
				self.mcdr_server.logger.exception(self.mcdr_server.tr('mcdr_server.console_input.parse_fail', text))
			else:
				self.mcdr_server.logger.debug('Parsed text from console input:')
				for line in parsed_result.format_text().splitlines():
					self.mcdr_server.logger.debug('    {}'.format(line))
				self.mcdr_server.reactor_manager.put_info(parsed_result)
		except (KeyboardInterrupt, EOFError, SystemExit, IOError) as e:
			self.mcdr_server.logger.debug('Exception {} {} caught in console_input()'.format(type(e), e))
			self.mcdr_server.interrupt()
		except:
			self.mcdr_server.logger.exception(self.mcdr_server.tr('mcdr_server.console_input.error'))
