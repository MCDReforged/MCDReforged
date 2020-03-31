# -*- coding: utf-8 -*-
import logging
import time
import traceback
import threading
from subprocess import Popen, PIPE

from utils import config, constant, logger, tool
from utils.plugin_manager import PluginManager
from utils.server_status import ServerStatus
from utils.server_interface import ServerInterface


class Server:
	def __init__(self):
		self.config = config.Config(constant.CONFIG_FILE)
		self.logger = logger.Logger(constant.NAME_SHORT)
		self.logger.set_file(constant.LOGGING_FILE)
		if self.config['debug_mode']:
			self.logger.set_level(logging.DEBUG)
		self.parser = self.load_parser(constant.PARSER_FOLDER, self.config['parser'])
		self.reactors = self.load_reactor(constant.REACTOR_FOLDER)
		self.console_input_thread = None
		self.process = None
		self.set_server_status(ServerStatus.STOPPED)
		self.server_interface = ServerInterface(self)
		self.plugin_manager = PluginManager(self, constant.PLUGIN_FOLDER)
		self.plugin_manager.load_plugins()
		self.flag_interrupt = False  # ctrl-c flag

	# Loaders

	@staticmethod
	def load_parser(path, parser_name):
		file_name = path + parser_name + '.py'
		return tool.load_source(file_name).parser

	@staticmethod
	def load_reactor(folder):
		reactors = []
		for file in tool.list_py_file(folder):
			module = tool.load_source(file)
			if hasattr(module, 'reactor'):
				reactors.append(module.reactor)
		return reactors

	# MCDR server

	def set_server_status(self, status):
		self.server_status = status
		self.logger.debug('Server status has set to "{}"'.format(status))

	def start_server(self):
		if self.process is not None:
			self.logger.warning('Server cannot start twice')
			return
		self.logger.info('Starting the server')
		try:
			self.process = Popen(self.config['start_command'], cwd=self.config['working_directory'],
				stdin=PIPE, stdout=PIPE, shell=True)
		except:
			self.logger.error('Fail to start the server')
			self.logger.error(traceback.format_exc())
			return False
		else:
			self.set_server_status(ServerStatus.RUNNING)
			self.logger.info(f'Server is running at PID {self.process.pid}')
			return True

	def start(self):
		if self.start_server():
			self.console_input_thread = threading.Thread(target=self.console_input)
			self.console_input_thread.setDaemon(True)
			self.console_input_thread.setName('Console')
			self.console_input_thread.start()
			self.run()

	def stop(self, forced=False, new_server_status=ServerStatus.STOPPING_BY_ITSELF):
		if self.process is None:
			self.logger.warning('Server cannot stop when terminated')
		self.set_server_status(new_server_status)
		if not forced:
			try:
				self.send(self.parser.STOP_COMMAND)
			except:
				self.logger.error('Error stopping server, force the server to stop now')
				forced = True
		if forced:
			self.process.kill()
			self.logger.info('Process killed')

	def send(self, text, ending='\n'):
		if type(text) is str:
			text = (text + ending).encode('utf8')
		if self.process	is not None:
			self.process.stdin.write(text)
			self.process.stdin.flush()
		else:
			self.logger.warning('Server has been terminated, cannot send command to its stdin')

	def receive(self):
		while True:
			if self.process.poll() is not None:
				return None
			try:
				text = next(iter(self.process.stdout))
			except StopIteration: # server process has stopped
				for i in range(100):
					if self.process.poll() is not None:
						break
					time.sleep(0.1)
					if i % 10 == 0:
						self.logger.info('Waiting for server process to exit')
				if self.server_status is ServerStatus.RUNNING:
					self.set_server_status(ServerStatus.STOPPING_BY_ITSELF)
				return None
			else:
				text = text.rstrip()
				if text != '':
					return text.decode('utf8')
				print('www')

	def tick(self):
		text = self.receive()
		if text is None:  # server process has been terminated
			return_code = self.process.poll()
			self.logger.info(f'Server exited with code {return_code}')
			self.process = None
			if self.server_status == ServerStatus.STOPPING_BY_ITSELF:
				self.logger.info('Server stopped by itself')
				self.set_server_status(ServerStatus.STOPPED)
			return

		print('[Server]', text)
		try:
			parsed_result = self.parser.parse_server_stdout(text)
		except:
			self.logger.warning('Fail to parse text from stdout of the server')
			self.logger.debug(traceback.format_exc())
		else:
			self.react(parsed_result)

	def run(self):
		while self.server_status != ServerStatus.STOPPED:
			try:
				if self.process is not None:
					self.tick()
				time.sleep(0.01)
			except KeyboardInterrupt:
				self.flag_interrupt = True
			except:
				if not self.flag_interrupt:
					self.logger.error(f'Error ticking {constant.NAME_SHORT}')
					self.logger.error(traceback.format_exc())
					self.stop()
				break
		if self.flag_interrupt:
			self.logger.info(f'{constant.NAME_SHORT} has been interrupted by user')
		self.logger.info('bye')

	# the thread for processing console input
	def console_input(self):
		try:
			while True:
				text = input()
				try:
					parsed_result = self.parser.parse_console_command(text)
					self.react(parsed_result)
				except:
					self.logger.error(f'Error processing console command {text}')
					self.logger.error(traceback.format_exc())
					self.stop()
					break
		except (KeyboardInterrupt, EOFError, SystemExit, IOError):
			self.flag_interrupt = True
			self.stop(forced=True)

	# react to a parsed info
	def react(self, info):
		for reactor in self.reactors:
			reactor.react(self, info)
