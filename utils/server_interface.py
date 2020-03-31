# -*- coding: utf-8 -*-
# An interface class for plugins to control the server
import time

from utils.server_status import ServerStatus


class ServerInterface:
	def __init__(self, server):
		self.server = server
		self.logger = server.logger

	# the same as MCD 1.0

	def start(self):
		self.server.start_server()

	def stop(self):
		self.server.stop(forced=False, new_server_status=ServerStatus.STOPPING_BY_PLUGIN)

	def execute(self, text):
		self.server.send(text)

	# without '\n' ending
	def send(self, text):
		self.server.send(text, ending='')

	def say(self, data):
		self.execute('tellraw @a {"text":"' + str(data) + '"}')

	def tell(self, player, data):
		self.execute('tellraw ' + player + ' {"text":"' + str(data) + '"}')

	# MCDR stuffs

	# wait until the server is able to start
	def wait_for_start(self):
		while self.server.process is not None:
			time.sleep(0.01)

	def restart(self):
		self.stop()
		self.wait_for_start()
		self.start()