import sys

from mcdreforged.constants import core_constant
from mcdreforged.mcdr_server import MCDReforgedServer


def run_mcdr():
	print('{} {} is starting up'.format(core_constant.NAME, core_constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(core_constant.NAME, core_constant.GITHUB_URL))

	try:
		mcdreforged_server = MCDReforgedServer()
	except Exception as e:
		print('Fail to initialize {}: ({}) {}'.format(core_constant.NAME_SHORT, type(e), e), file=sys.stderr)
		raise

	if mcdreforged_server.is_initialized():
		mcdreforged_server.start()
	else:
		# If it's not initialized, config file or permission file is missing
		# Just don't do anything to let the user check the files
		pass
