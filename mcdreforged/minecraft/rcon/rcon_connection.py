"""
Simple rcon client implement
Reference: https://wiki.vg/RCON
"""
import dataclasses
import socket
import struct
import time
from logging import Logger
from threading import RLock
from typing import Optional


class _RequestId:
	DEFAULT = 0
	LOGIN_FAIL = -1


class _PacketType:
	COMMAND_RESPONSE = 0
	COMMAND_REQUEST = 2
	LOGIN_REQUEST = 3
	ENDING_PACKET = 100


@dataclasses.dataclass(frozen=True)
class Packet:
	request_id: int
	packet_type: int
	payload: str

	def flush(self) -> bytes:
		data = struct.pack('<ii', self.request_id, self.packet_type) + bytes(self.payload + '\x00\x00', encoding='utf8')
		return struct.pack('<i', len(data)) + data


class RconConnection:
	"""
	A simply rcon client for connect to any Minecraft servers that supports rcon protocol
	"""

	BUFFER_SIZE = 2 ** 10

	def __init__(self, address: str, port: int, password: str, *, logger: Optional[Logger] = None):
		"""
		Create a rcon client instance

		:param address: The address of the rcon server
		:param port: The port if the rcon server
		:param password: The password of the rcon connection
		:keyword logger: Optional, an instance of ``logging.Logger``.
			It's used to output some warning information like failing to receive a packet
		"""
		self.logger = logger
		self.address = address
		self.port = port
		self.password = password
		self.socket: Optional[socket.socket] = None
		self.command_lock = RLock()

	def __del__(self):
		self.disconnect()

	def __send(self, data: Packet):
		self.socket.send(data.flush())
		time.sleep(0.03)  # MC-72390

	def __receive(self, length: int) -> bytes:
		data = bytes()
		while len(data) < length:
			data += self.socket.recv(min(self.BUFFER_SIZE, length - len(data)))
		return data

	def __receive_packet(self) -> Packet:
		length = struct.unpack('<i', self.__receive(4))[0]
		data = self.__receive(length)
		packet = Packet(
			request_id=struct.unpack('<i', data[0:4])[0],
			packet_type=struct.unpack('<i', data[4:8])[0],
			payload=data[8:-2].decode('utf8'),
		)
		return packet

	def connect(self) -> bool:
		"""
		Start a connection to the rcon server and try to log in

		:return: If connect and login success
		"""
		if self.socket is not None:
			try:
				self.disconnect()
			except Exception:
				pass
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.address, self.port))
		self.__send(Packet(_RequestId.DEFAULT, _PacketType.LOGIN_REQUEST, self.password))
		success = self.__receive_packet().request_id != _RequestId.LOGIN_FAIL
		if not success:
			self.disconnect()
		return success

	def disconnect(self):
		"""
		Disconnect from the server
		"""
		if self.socket is None:
			return
		self.socket.close()
		self.socket = None

	def send_command(self, command: str, max_retry_time: int = 3) -> Optional[str]:
		"""
		Send a command to the rcon server

		:param command: The command you want to send to the server
		:param max_retry_time: The maximum retry time of the operation
		:return: The command execution result form the server, or None if *max_retry_time* retries exceeded
		"""
		with self.command_lock:
			for i in range(max_retry_time):
				try:
					self.__send(Packet(_RequestId.DEFAULT, _PacketType.COMMAND_REQUEST, command))
					self.__send(Packet(_RequestId.DEFAULT, _PacketType.ENDING_PACKET, 'lol'))
					result = ''
					while True:
						packet = self.__receive_packet()
						if packet.payload == 'Unknown request {}'.format(hex(_PacketType.ENDING_PACKET)[2:]):
							break
						result += packet.payload
					return result
				except Exception:
					if self.logger is not None:
						self.logger.warning('Rcon Fail to received packet')
					try:
						self.disconnect()
						if self.connect():  # next try
							continue
					except Exception:
						pass
					break
		return None


if __name__ == '__main__':
	rcon = RconConnection('localhost', 25575, 'rcon_34ft786cbsqd')
	ok = rcon.connect()
	print('Login success: {}'.format(ok))
	if ok:
		while True:
			print('Server ->', rcon.send_command(input('Server <- ')))
