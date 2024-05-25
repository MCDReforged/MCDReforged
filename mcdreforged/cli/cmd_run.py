import sys

from mcdreforged.constants import core_constant
from mcdreforged.mcdr_server import MCDReforgedServer
from mcdreforged.mcdr_server_args import MCDReforgedServerArgs


def run_mcdr(args: MCDReforgedServerArgs):
	print('{} {} is starting up'.format(core_constant.NAME, core_constant.VERSION))
	print('{} is open source, u can find it here: {}'.format(core_constant.NAME, core_constant.GITHUB_URL))

	try:
		mcdreforged_server = MCDReforgedServer(args)
	except Exception as e:
		print('Fail to initialize {}: ({}) {}'.format(core_constant.NAME_SHORT, type(e), e), file=sys.stderr)
		print('Args: {}'.format(args), file=sys.stderr)
		raise

	if mcdreforged_server.is_initialized():
		mcdreforged_server.run_mcdr()
	else:
		# If it's not initialized, config file or permission file is missing
		# Just don't do anything to let the user check the files
		pass
