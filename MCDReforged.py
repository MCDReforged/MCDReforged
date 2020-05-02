# -*- coding: utf-8 -*-
import traceback
import sys

try:
	if sys.version_info.major < 3:
		print('Python 3.6+ is needed')
		raise Exception('Python is too old')
	try:
		from utils.server import Server
		from utils import constant
	except ModuleNotFoundError:
		print('It seems that you have not installed all require modules')
		raise

	if __name__ == '__main__':
		print('{} {} is starting up'.format(constant.NAME_SHORT, constant.VERSION))
		print('{} is open source, u can find it here: {}'.format(constant.NAME_SHORT, constant.GITHUB_URL))
		print('{} is still in development, it may not work well'.format(constant.NAME_SHORT))
		try:
			server = Server()
		except Exception as e:
			print('Fail to initialize {}'.format(constant.NAME_SHORT))
			raise
		else:
			server.start()
except:
	print(traceback.format_exc())
	input('Exception occurred, press Enter to exit')
