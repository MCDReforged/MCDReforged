"""
Simple rcon client implement
"""
import socket
import struct
import time
from threading import RLock


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


class Rcon:
	BUFFER_SIZE = 2**10

	def __init__(self, address, port, password, logger=None):
		self.logger = logger
		self.address = address
		self.port = port
		self.password = password
		self.socket = None
		self.command_lock = RLock()

	def __del__(self):
		self.disconnect()

	def send(self, data):
		if type(data) is Packet:
			data = data.flush()
		self.socket.send(data)
		time.sleep(0.03)  # MC-72390

	def receive(self, length):
		data = bytes()
		while len(data) < length:
			data += self.socket.recv(min(self.BUFFER_SIZE, length - len(data)))
		return data

	def receive_packet(self):
		length = struct.unpack('<i', self.receive(4))[0]
		data = self.receive(length)
		packet = Packet()
		packet.packet_id = struct.unpack('<i', data[0:4])[0]
		packet.packet_type = struct.unpack('<i', data[4:8])[0]
		packet.payload = data[8:-2].decode('utf8')
		return packet

	def connect(self):
		if self.socket is not None:
			try:
				self.disconnect()
			except:
				pass
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket.connect((self.address, self.port))
		self.send(Packet(PacketType.LOGIN_REQUEST, self.password))
		success = self.receive_packet().packet_id != PacketType.LOGIN_FAIL
		if not success:
			self.disconnect()
		return success

	def disconnect(self):
		if self.socket is None:
			return
		self.socket.close()
		self.socket = None

	def __send_command(self, command, depth, max_retry_time):
		self.command_lock.acquire()
		try:
			self.send(Packet(PacketType.COMMAND_REQUEST, command))
			self.send(Packet(PacketType.ENDING_PACKET, 'lol'))
			result = ''
			while True:
				packet = self.receive_packet()
				if packet.payload == 'Unknown request {}'.format(hex(PacketType.ENDING_PACKET)[2:]):
					break
				result += packet.payload
			return result
		except:
			if self.logger is not None:
				self.logger.warning('Rcon Fail to received packet')
			try:
				self.disconnect()
				if self.connect() and depth < max_retry_time:
					return self.__send_command(command, depth + 1, max_retry_time)
			except:
				pass
			return None
		finally:
			self.command_lock.release()

	def send_command(self, command, max_retry_time=3):
		return self.__send_command(command, 0, max_retry_time)


if __name__ == '__main__':
	rcon = Rcon('localhost', 25575, 'password')
	print('Login success? ', rcon.connect())
	while True:
		print('->', rcon.send_command(input('<- ')))
