# -*- coding: utf-8 -*-
import socket
import struct
import time
from threading import Lock

from utils.rcon.packet import Packet, PacketType


class Rcon:
	BUFFER_SIZE = 2**10

	def __init__(self, address, port, password, logger=None):
		self.logger = logger
		self.address = address
		self.port = port
		self.password = password
		self.socket = None
		self.command_lock = Lock()

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
			return False
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

	def send_command(self, command):
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
			return None
		finally:
			self.command_lock.release()


if __name__ == '__main__':
	rcon = Rcon('localhost', 25575, 'password')
	print('Login success? ', rcon.connect())
	while True:
		print('>', rcon.send_command(input('< ')))
