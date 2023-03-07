from mcdreforged.constants import core_constant


def show_version(*, quiet: bool = False):
	if quiet:
		return
	print('{} {}'.format(core_constant.NAME, core_constant.VERSION))
