"""
Simple rcon client implement
"""
import socket
import struct
import time
from logging import Logger
from threading import RLock
from typing import Optional


class PacketType:
	COMMAND_RESPONSE = 0
	COMMAND_REQUEST = 2
	LOGIN_REQUEST = 3
	LOGIN_FAIL = -1
	ENDING_PACKET = 100


class Packet:
	def __init__(self, packet_type=None, payload=None):
		self.packet_id = 0
		self.packet_type = packet_type
		self.payload = payload

	def flush(self):
		data = struct.pack('<ii', self.packet_id, self.packet_type) + bytes(self.payload + '\x00\x00', encoding='utf8')
		return struct.pack('<i', len(data)) + data


class RconConnection:
	BUFFER_SIZE = 2**10

	def __init__(self, address: str, port: int, password: str, *, logger: Optional[Logger] = None):
		self.logger = logger
		self.address = address
		self.port = port
		self.password = password
		self.socket = None
		self.command_lock = RLock()

	def __del__(self):
		self.disconnect()

	def __send(self, data):
		if type(data) is Packet:
			data = data.flush()
		self.socket.send(data)
		time.sleep(0.03)  # MC-72390

	def __receive(self, length):
		data = bytes()
		while len(data) < length:
			data += self.socket.recv(min(self.BUFFER_SIZE, length - len(data)))
		return data

	def __receive_packet(self):
		length = struct.unpack('<i', self.__receive(4))[0]
		data = self.__receive(length)
		packet = Packet()
		packet.packet_id = struct.unpack('<i', data[0:4])[0]
		packet.packet_type = struct.unpack('<i', data[4:8])[0]
		packet.payload = data[8:-2].decode('utf8')
		return packet

	def connect(self) -> bool:
		if self.socket is not None:
			try:
				self.disconnect()
			except:
				pass
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.address, self.port))
		self.__send(Packet(PacketType.LOGIN_REQUEST, self.password))
		success = self.__receive_packet().packet_id != PacketType.LOGIN_FAIL
		if not success:
			self.disconnect()
		return success

	def disconnect(self):
		if self.socket is None:
			return
		self.socket.close()
		self.socket = None

	def send_command(self, command: str, max_retry_time: int = 3) -> Optional[str]:
		with self.command_lock:
			for i in range(max_retry_time):
				try:
					self.__send(Packet(PacketType.COMMAND_REQUEST, command))
					self.__send(Packet(PacketType.ENDING_PACKET, 'lol'))
					result = ''
					while True:
						packet = self.__receive_packet()
						if packet.payload == 'Unknown request {}'.format(hex(PacketType.ENDING_PACKET)[2:]):
							break
						result += packet.payload
					return result
				except:
					if self.logger is not None:
						self.logger.warning('Rcon Fail to received packet')
					try:
						self.disconnect()
						if self.connect():  # next try
							continue
					except:
						pass
					break
		return None


if __name__ == '__main__':
	rcon = RconConnection('localhost', 25575, 'password')
	print('Login success? ', rcon.connect())
	while True:
		print('Server ->', rcon.send_command(input('Server <- ')))
