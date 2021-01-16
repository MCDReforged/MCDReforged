"""
Entry for MCDR
"""
import sys


def main():
	python_version = sys.version_info.major + sys.version_info.minor * 0.1
	if python_version < 3.6:
		print('Python 3.6+ is needed')
		raise Exception('Python version {} is too old'.format(python_version))

	try:
		from mcdreforged import constant
		from mcdreforged.mcdr_server import MCDReforgedServer
	except ModuleNotFoundError:
		print('It seems that you have not installed all require modules')
		raise

	print('{} {} is starting up'.format(constant.NAME, constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(constant.NAME, constant.GITHUB_URL))
	print('{} is still in development, it may not work well'.format(constant.NAME))
	try:
		mcdreforged_server = MCDReforgedServer()
	except:
		print('Fail to initialize {}'.format(constant.NAME_SHORT))
		raise
	else:
		if mcdreforged_server.is_initialized():
			mcdreforged_server.start()
		else:
			# If it's not initialized, config file or permission file is missing
			# Just dont do anything to let the user to check the files
			pass


if __name__ == '__main__':
	sys.exit(main())
