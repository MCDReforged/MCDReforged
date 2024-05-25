"""
A more flexible interface for rcon support
It also wrap everything to make sure no exception can escape
"""
from typing import TYPE_CHECKING, Optional

from mcdreforged.minecraft.rcon.rcon_connection import RconConnection

if TYPE_CHECKING:
	from mcdreforged.mcdr_server import MCDReforgedServer


class RconManager:
	def __init__(self, mcdr_server: 'MCDReforgedServer'):
		self.mcdr_server = mcdr_server
		self.logger = mcdr_server.logger
		self.rcon: Optional[RconConnection] = None
		self.__tr = mcdr_server.create_internal_translator('rcon_manager').tr

	def is_running(self) -> bool:
		return self.rcon is not None and self.rcon.socket is not None

	def connect(self, address: str, port: int, password: str):
		if self.is_running():
			self.disconnect()
		self.rcon = RconConnection(address, port, password, logger=self.logger)
		try:
			success = self.rcon.connect()
		except Exception as e:
			self.logger.exception(self.__tr('connect.connection_fail', e))
			self.rcon = None
		else:
			if success:
				self.logger.info(self.__tr('connect.connected'))
			else:
				self.logger.info(self.__tr('connect.wrong_password'))

	def disconnect(self):
		if self.is_running():
			try:
				self.rcon.disconnect()
				self.logger.info(self.__tr('disconnect.disconnected'))
			except Exception:
				self.mcdr_server.logger.error(self.__tr('disconnect.disconnect_fail'))
		self.rcon = None

	def send_command(self, command: str) -> Optional[str]:
		if self.is_running():
			return self.rcon.send_command(command)
		else:
			return None
