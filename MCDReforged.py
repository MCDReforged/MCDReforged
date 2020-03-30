# -*- coding: utf-8 -*-

from .utils.server import Server


def info():
	print('MCDReforge starting')


info()
try:
	server = Server()
except:
	print('fail to initialize the server')
	raise

server.start()

