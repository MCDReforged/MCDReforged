"""
Simple rcon client implement
Reference: https://wiki.vg/RCON
"""
import contextlib
import dataclasses
import socket
import struct
from logging import Logger
from threading import RLock
from typing import Optional, List, ClassVar


class _RequestId:
	LOGIN = 0
	COMMAND = 1
	ENDING_PROBE = 2
	LOGIN_FAIL = -1


class _PacketType:
	COMMAND_RESPONSE = 0
	COMMAND_REQUEST = 2
	LOGIN_REQUEST = 3
	ENDING_PACKET = 100  # an invalid id


@dataclasses.dataclass(frozen=True)
class Packet:
	request_id: int
	packet_type: int
	payload: str

	def dump(self) -> bytes:
		return struct.pack('<ii', self.request_id, self.packet_type) + bytes(self.payload + '\x00\x00', encoding='utf8')

	def dump_with_length_header(self) -> bytes:
		data = self.dump()
		return struct.pack('<i', len(data)) + data

	@classmethod
	def load(cls, data: bytes) -> 'Packet':
		"""data is without the length header"""
		return Packet(
			request_id=struct.unpack('<i', data[0:4])[0],
			packet_type=struct.unpack('<i', data[4:8])[0],
			payload=data[8:-2].decode('utf8'),
		)


class RconConnection:
	"""
	A simply rcon client for connect to any Minecraft servers that supports rcon protocol
	"""

	BUFFER_SIZE: ClassVar[int] = 4096

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
		assert self.socket is not None
		self.socket.sendall(data.dump_with_length_header())

	def __receive(self, length: int) -> bytes:
		assert self.socket is not None
		fragments: List[bytes] = []
		read_len = 0
		while read_len < length:
			buf = self.socket.recv(min(self.BUFFER_SIZE, length - read_len))
			if not buf:
				raise ConnectionError(f'Connection closed by peer while reading data, expect {length}, read {read_len}')
			read_len += len(buf)
			fragments.append(buf)
		return b''.join(fragments)

	def __receive_packet(self) -> Packet:
		length = struct.unpack('<i', self.__receive(4))[0]
		data = self.__receive(length)
		return Packet.load(data)

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
		self.__send(Packet(_RequestId.LOGIN, _PacketType.LOGIN_REQUEST, self.password))
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
					self.__send(Packet(_RequestId.COMMAND, _PacketType.COMMAND_REQUEST, command))
					self.__send(Packet(_RequestId.ENDING_PROBE, _PacketType.ENDING_PACKET, 'lol'))
					result_parts: List[str] = []
					while (packet := self.__receive_packet()).request_id == _RequestId.COMMAND:
						result_parts.append(packet.payload)
					return ''.join(result_parts)
				except Exception as e:
					if self.logger is not None:
						self.logger.warning(f'Rcon fail to receive packet: {e}')
					with contextlib.suppress(Exception):
						self.disconnect()
						if self.connect():  # next try
							continue
					break
		return None


if __name__ == '__main__':
	rcon = RconConnection('localhost', 25575, 'rcon_34ft786cbsqd')
	ok = rcon.connect()
	print('Login success: {}'.format(ok))
	if ok:
		while True:
			print('Server ->', rcon.send_command(input('Server <- ')))
