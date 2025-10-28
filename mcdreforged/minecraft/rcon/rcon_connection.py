"""
Simple rcon client implement
Reference: https://minecraft.wiki/w/RCON
"""
import asyncio
import contextlib
import dataclasses
import os
import socket
import struct
from logging import Logger
from threading import RLock
from typing import Optional, List, ClassVar


class RconException(Exception):
	pass


class RconAuthenticationFail(RconException):
	pass


class RconIncompleteReadError(RconException):
	pass


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


@dataclasses.dataclass(frozen=True)
class RconConnectionConfig:
	address: str
	port: int
	password: str


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
		self.config = RconConnectionConfig(address, port, password)
		self.logger = logger
		self.socket: Optional[socket.socket] = None
		self.command_lock = RLock()

	def __del__(self):
		self.disconnect()

	def __enter__(self) -> 'RconConnection':
		success = self.connect()
		if not success:
			raise RconAuthenticationFail('RCON authentication failed')
		return self

	def __exit__(self, exc_type, exc_val, exc_tb):
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
				raise RconIncompleteReadError(f'Connection closed by peer while reading data, expect {length}, read {read_len}')
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
		with contextlib.suppress(Exception):
			self.disconnect()
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.config.address, self.config.port))
		self.__send(Packet(_RequestId.LOGIN, _PacketType.LOGIN_REQUEST, self.config.password))
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


class AsyncRconConnection:
	@dataclasses.dataclass(frozen=True)
	class __Connection:
		reader: asyncio.StreamReader
		writer: asyncio.StreamWriter

	def __init__(self, address: str, port: int, password: str, *, logger: Optional[Logger] = None):
		"""
		Create a rcon client instance

		:param address: The address of the rcon server
		:param port: The port if the rcon server
		:param password: The password of the rcon connection
		:keyword logger: Optional, an instance of ``logging.Logger``.
			It's used to output some warning information like failing to receive a packet

		.. versionadded:: v2.16.0
		"""
		self.config = RconConnectionConfig(address, port, password)
		self.logger = logger
		self.connection: Optional[AsyncRconConnection.__Connection] = None
		self.command_lock = asyncio.Lock()

	async def __aenter__(self) -> 'AsyncRconConnection':
		success = await self.connect()
		if not success:
			raise RconAuthenticationFail('RCON authentication failed')
		return self

	async def __aexit__(self, exc_type, exc_val, exc_tb):
		await self.disconnect()

	async def __send(self, data: Packet):
		assert self.connection is not None
		self.connection.writer.write(data.dump_with_length_header())
		await self.connection.writer.drain()

	async def __receive(self, length: int) -> bytes:
		assert self.connection is not None
		try:
			return await self.connection.reader.readexactly(length)
		except asyncio.IncompleteReadError as e:
			raise RconIncompleteReadError(f'Connection closed by peer while reading data, expect {length}, read {len(e.partial)}')

	async def __receive_packet(self) -> Packet:
		length = struct.unpack('<i', await self.__receive(4))[0]
		data = await self.__receive(length)
		return Packet.load(data)

	async def connect(self) -> bool:
		with contextlib.suppress(Exception):
			await self.disconnect()
		reader, writer = await asyncio.open_connection(self.config.address, self.config.port)
		self.connection = self.__Connection(reader, writer)
		await self.__send(Packet(_RequestId.LOGIN, _PacketType.LOGIN_REQUEST, self.config.password))
		success = (await self.__receive_packet()).request_id != _RequestId.LOGIN_FAIL
		if not success:
			await self.disconnect()
		return success

	async def disconnect(self):
		if (conn := self.connection) is None:
			return
		self.connection = None
		conn.writer.close()
		await conn.writer.wait_closed()

	async def send_command(self, command: str, max_retry_time: int = 3) -> Optional[str]:
		"""
		Send a command to the rcon server

		:param command: The command you want to send to the server
		:param max_retry_time: The maximum retry time of the operation
		:return: The command execution result form the server, or None if *max_retry_time* retries exceeded
		"""
		async with self.command_lock:
			for i in range(max_retry_time):
				try:
					await self.__send(Packet(_RequestId.COMMAND, _PacketType.COMMAND_REQUEST, command))
					await self.__send(Packet(_RequestId.ENDING_PROBE, _PacketType.ENDING_PACKET, 'lol'))
					result_parts: List[str] = []
					while (packet := await self.__receive_packet()).request_id == _RequestId.COMMAND:
						result_parts.append(packet.payload)
					return ''.join(result_parts)
				except Exception as e:
					if self.logger is not None:
						self.logger.warning(f'Rcon fail to receive packet: {e}')
					with contextlib.suppress(Exception):
						await self.disconnect()
						if await self.connect():  # next try
							continue
					break
		return None


def __main():
	with RconConnection(
		address=os.getenv('MCDR_RCON_TEST_ADDRESS', 'localhost'),
		port=int(os.getenv('MCDR_RCON_TEST_PORT', '25575')),
		password=os.getenv('MCDR_RCON_TEST_PASSWORD', 'eXamp1eRC0Npazzwalled'),
	) as rcon:
		while True:
			print('Server ->', rcon.send_command(input('Server <- ')))


async def __async_main():
	async with AsyncRconConnection(
		address=os.getenv('MCDR_RCON_TEST_ADDRESS', 'localhost'),
		port=int(os.getenv('MCDR_RCON_TEST_PORT', '25575')),
		password=os.getenv('MCDR_RCON_TEST_PASSWORD', 'eXamp1eRC0Npazzwalled'),
	) as rcon:
		while True:
			print('Server ->', await rcon.send_command(input('Server <- ')))


if __name__ == '__main__':
	with contextlib.suppress(KeyboardInterrupt):
		__main()
