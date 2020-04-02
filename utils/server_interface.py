# -*- coding: utf-8 -*-
# An interface class for plugins to control the server
import time

from utils.info import Info
from utils.server_status import ServerStatus


def format_string(data):
	return str(data).replace('\\', '\\\\').replace('"', '\\"')


class ServerInterface:
	MCDR = True  # Identifier for plugins

	def __init__(self, server):
		self.__server = server
		self.logger = server.logger

	# the same as MCD 1.0

	def start(self):
		self.__server.start_server()

	def stop(self):
		self.__server.stop(forced=False, new_server_status=ServerStatus.STOPPING_BY_PLUGIN)

	def execute(self, text):
		self.logger.debug('Plugin executed "{}"'.format(text))
		self.__server.send(text)

	# without '\n' ending
	def send(self, text):
		self.logger.debug('Plugin sent "{}"'.format(text))
		self.__server.send(text, ending='')

	def say(self, data):
		self.execute('tellraw @a {{"text":"{}"}}'.format(format_string(data)))

	def tell(self, player, data):
		self.execute('tellraw {} {{"text":"{}"}}'.format(player, format_string(data)))

	# MCDR stuffs

	# if the server is running
	def is_running(self):
		return self.__server.is_running()

	# wait until the server is able to start
	def wait_for_start(self):
		while self.is_running():
			time.sleep(0.01)

	# restart the server
	def restart(self):
		self.stop()
		self.wait_for_start()
		self.start()

	# stop and exit the server
	def stop_exit(self):
		self.__server.stop(forced=False)

	# return the permission level number the object has
	# the object can be Info instance or player name
	def get_permission_level(self, obj):
		if type(obj) is Info:  # Info instance
			return self.__server.permission_manager.get_info_level(obj)
		elif type(obj) is str:  # player name
			return self.__server.permission_manager.get_player_level(obj)
		else:
			return None

	# if MCDR's rcon is running
	def is_rcon_running(self):
		return self.__server.rcon_manager.is_running()

	# send command through rcon
	# return the result server returned from rcon
	# if rcon is not running return None
	def rcon_query(self, command):
		return self.__server.rcon_manager.send_command(command)

