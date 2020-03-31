# -*- coding: utf-8 -*-
# An interface class for plugins to control the server
from utils.server_status import ServerStatus


class ServerInterface:
	def __init__(self, server):
		self.server = server

	def start(self):
		pass

	def stop(self):
		self.server.stop(force=False, new_server_status=ServerStatus.RESTARTING)

	def execute(self, text):
		self.server.send(text)

	# without '\n' ending
	def send(self, text):
		self.server.send(text, ending='')

	def say(self, data):
		self.execute('tellraw @a {"text":"' + str(data) + '"}')

	def tell(self, player, data):
		self.execute('tellraw ' + player + ' {"text":"' + str(data) + '"}')
