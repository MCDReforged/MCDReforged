# -*- coding: utf-8 -*-
from utils.rcon.rcon import Rcon


class RconManager:
	def __init__(self, server):
		self.server = server
		self.logger = server.logger
		self.rcon = None

	def is_running(self):
		return self.rcon is not None and self.rcon.socket is not None

	def connect(self, address, port, password):
		if self.is_running():
			self.disconnect()
		self.rcon = Rcon(address, port, str(password), self.logger)
		try:
			success = self.rcon.connect()
		except Exception as e:
			self.logger.info(self.server.t('rcon_manager.connect.connection_fail', e))
			self.rcon = None
		else:
			if success:
				self.logger.info(self.server.t('rcon_manager.connect.connected'))
			else:
				self.logger.info(self.server.t('rcon_manager.connect.wrong_password'))

	def disconnect(self):
		if self.is_running():
			self.rcon.disconnect()
			self.logger.info(self.server.t('rcon_manager.disconnect.disconnected'))
		self.rcon = None

	def send_command(self, command):
		if self.is_running():
			return self.rcon.send_command(command)
		else:
			return None
