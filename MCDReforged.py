# -*- coding: utf-8 -*-
import traceback
import sys
import os


try:
	if sys.version_info.major + sys.version_info.minor * 0.1 < 3.6:
		print('Python 3.6+ is needed')
		raise Exception('Python is too old')

	if not os.path.isdir('utils'):
		print('Cannot found necessary folder "utils", seems that you have launched it in a wrong directory')
		print('Current working directory: {}'.format(os.getcwd()))
		raise Exception('Path not right')

	try:
		from utils import constant
		from utils.server import Server
	except ModuleNotFoundError:
		print('It seems that you have not installed all require modules')
		raise

	if __name__ == '__main__':
		print('{} {} is starting up'.format(constant.NAME, constant.VERSION))
		print('{} is open source, u can find it here: {}'.format(constant.NAME, constant.GITHUB_URL))
		print('{} is still in development, it may not work well'.format(constant.NAME))
		try:
			server = Server()
		except Exception as e:
			print('Fail to initialize {}'.format(constant.NAME_SHORT))
			raise
		else:
			server.start()

except:
	traceback.print_exc()
	input('Exception occurred, press Enter to exit')
