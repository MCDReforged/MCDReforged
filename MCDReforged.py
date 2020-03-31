# -*- coding: utf-8 -*-
from utils.server import Server
from utils import constant

if __name__ == '__main__':
	print('MCDReforged starting')
	try:
		server = Server()
	except:
		print(f'Fail to initialize {constant.NAME_SHORT}')
		raise

	server.start()
