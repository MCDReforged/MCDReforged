# -*- coding: utf-8 -*-
import traceback
import sys
import os
from multiprocessing import set_start_method, Process, Pipe
from multiprocessing.connection import Connection
from subprocess import Popen


def run(child_conn: Connection, fileno):
	sys.stdin = os.fdopen(fileno)
	try:
		from utils import constant
		from utils.server import Server
		from utils.server_status import ExitType
	except ModuleNotFoundError:
		print('It seems that you have not installed all require modules')
		raise

	print('{} {} is starting up'.format(constant.NAME, constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(constant.NAME, constant.GITHUB_URL))
	print('{} is still in development, it may not work well'.format(constant.NAME))
	server_process = child_conn.recv()  # type: Popen
	return_data = None
	try:
		server = Server()
	except:
		print('Fail to initialize {}'.format(constant.NAME_SHORT))
		traceback.print_exc()
		if type(server_process) is Popen:
			while True:
				try:
					choice = input('Retry starting up (y) or kill the server process and exit (n)?\n(y/n): ').lower()
				except (KeyboardInterrupt, EOFError, SystemExit):
					choice = 'n'
					break
				else:
					if choice in ['y', 'n']:
						break
			if choice == 'y':
				return_data = server_process
			else:
				server_process.kill()
	else:
		server.start(server_process)
		if server.exit_type in [ExitType.RESTART]:
			return_data = server.process
	finally:
		try:
			child_conn.send(return_data)
		except:
			if type(return_data) is Popen:
				return_data.kill()
			child_conn.send(None)
			raise


def main():
	set_start_method('spawn')
	server_process = None
	while True:
		parent_conn, child_conn = Pipe()
		p = Process(target=run, args=(child_conn, sys.stdin.fileno()))
		p.daemon = True
		parent_conn.send(server_process)
		p.start()
		p.join()
		server_process = parent_conn.recv()
		if server_process is None:
			break
		print()


if __name__ == '__main__':
	try:
		python_version = sys.version_info.major + sys.version_info.minor * 0.1
		if python_version < 3.6:
			print('Python 3.6+ is needed')
			raise Exception('Python version {} is too old'.format(python_version))

		if not os.path.isfile(os.path.join('utils', '__init__.py')):
			print('Cannot found necessary module folder "utils", seems that you have launched it in a wrong directory')
			print('Current working directory: {}'.format(os.getcwd()))
			raise Exception('Wrong working directory')

		main()

	except:
		traceback.print_exc()
		input('Exception occurred, press Enter to exit')
		exit(1)
