# -*- coding: utf-8 -*-
import struct


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
