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
		from mcdreforged.constants import core_constant
		from mcdreforged.mcdr_server import MCDReforgedServer
	except ModuleNotFoundError:
		print('It seems that you have not installed all require modules')
		raise

	print('{} {} is starting up'.format(core_constant.NAME, core_constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(core_constant.NAME, core_constant.GITHUB_URL))
	try:
		mcdreforged_server = MCDReforgedServer()
	except:
		print('Fail to initialize {}'.format(core_constant.NAME_SHORT))
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
