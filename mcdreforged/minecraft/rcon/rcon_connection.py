"""
Simple rcon client implement
Reference: https://minecraft.wiki/w/RCON
"""
import contextlib
import dataclasses
import logging
import os
import socket
import struct
import sys
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
		self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
		self.socket.connect((self.address, self.port))
		self.socket.settimeout(60)
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
		:return: The command execution result from the server, or None if *max_retry_time* retries exceeded
		"""
		def send_once() -> str:
			"""
			Workaround for Minecraft's buggy implementation of RCON

			1. Purpose of ENDING_PROBE:
			   Minecraft splits long RCON responses into multiple packets,
			   but does not provide a clear termination signal (e.g., an empty packet) when the response ends.
			   We send an extra `ENDING_PROBE` packet to serve as a delimiter to detect the end of the response stream

			2. Why send ENDING_PROBE later:
			   The MC server requires each TCP read to obtain EXACTLY one complete RCON packet,
			   reading partial or multiple packets causes a disconnect or data loss.
			   Therefore, we cannot send the COMMAND and ENDING_PROBE in one go.
			   We must ensure the server has finished reading the COMMAND packet before sending the ENDING_PROBE.
			   We achieve this by waiting for the first response packet before sending the probe

		    See also: https://github.com/MCDReforged/MCDReforged/pull/411#issuecomment-3735273034
			"""

			self.__send(Packet(_RequestId.COMMAND, _PacketType.COMMAND_REQUEST, command))
			result_parts: List[str] = []

			# Even for empty response, Minecraft itself will send a response with empty payload
			# So it's guaranteed that at least one response packet will be received for our COMMAND packet
			ending_probe_sent = False
			while (packet := self.__receive_packet()).request_id == _RequestId.COMMAND:
				result_parts.append(packet.payload)
				if self.logger:
					self.logger.debug(f'Rcon received command response with utf8 len {len(packet.payload)}')
				if not ending_probe_sent:
					# Minecraft has finished processing the COMMAND packet, we're safe to send our ending probe packet
					# XXX: break if len < 4096 as a fast path?
					self.__send(Packet(_RequestId.ENDING_PROBE, _PacketType.ENDING_PACKET, 'lol'))
					ending_probe_sent = True
			return ''.join(result_parts)

		with self.command_lock:
			for i in range(max_retry_time):
				try:
					return send_once()
				except Exception as e:
					if self.logger is not None:
						self.logger.warning(f'Rcon fail to receive packet ({i + 1} / {max_retry_time}): {e}')

				with contextlib.suppress(Exception):
					self.disconnect()
					try:
						if self.connect():  # next try
							continue
					except Exception as e:
						if self.logger is not None:
							self.logger.error(f'Rcon reconnect failed, no more retry: {e}')
				break
		return None


def __main():
	rcon = RconConnection(
		address=os.getenv('MCDR_RCON_TEST_ADDRESS', 'localhost'),
		port=int(os.getenv('MCDR_RCON_TEST_PORT', '25575')),
		password=os.getenv('MCDR_RCON_TEST_PASSWORD', 'eXamp1eRC0Npazzwalled'),
		logger=logging.getLogger(__name__),
	)

	ok = rcon.connect()
	print('Login success: {}'.format(ok))
	if not ok:
		sys.exit(1)

	try:
		while True:
			print('Server ->', rcon.send_command(input('Server <- ')))
	except KeyboardInterrupt:
		pass
	rcon.disconnect()


if __name__ == '__main__':
	__main()
