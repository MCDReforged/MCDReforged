import queue
import time

from utils import constant, tool


class ReactorManager:
	def __init__(self, server):
		self.server = server
		self.info_queue = queue.Queue(maxsize=constant.MAX_INFO_QUEUE_SIZE)
		self.reactors = self.load_reactor(constant.REACTOR_FOLDER)
		self.last_queue_full_warn_time = None

	def load_reactor(self, folder):
		reactors = []
		for file in tool.list_file(folder, constant.REACTOR_FILE_SUFFIX):
			module = tool.load_source(file)
			if callable(getattr(module, 'get_reactor', None)):
				reactors.append(module.get_reactor(self.server))
		return reactors

	def put_info(self, info):
		try:
			self.info_queue.put_nowait(info)
		except queue.Full:
			current_time = time.time()
			logging_method = self.server.logger.debug
			if self.last_queue_full_warn_time is None or current_time - self.last_queue_full_warn_time >= constant.REACTOR_QUEUE_FULL_WARN_INTERVAL_SEC:
				logging_method = self.server.logger.warning
				self.last_queue_full_warn_time = current_time
			logging_method(self.server.t('server.info_queue.full'))

	def run(self):
		"""
		the thread for looping to react to parsed info
		"""
		while not self.server.is_interrupt() and not self.server.is_mcdr_exit():
			try:
				info = self.info_queue.get(timeout=0.01)
			except queue.Empty:
				pass
			else:
				for reactor in self.reactors:
					try:
						reactor.react(info)
					except:
						self.server.logger.exception(self.server.t('server.react.error', type(reactor).__name__))
