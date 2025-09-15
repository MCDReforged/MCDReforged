__all__ = ['entrypoint']


def entrypoint():
	"""
	The one and only entrypoint for MCDR

	All MCDR launches start from here
	"""
	from mcdreforged.mcdr_boostrap import boostrap
	boostrap()

	from mcdreforged.cli import cli_entry
	cli_entry.cli_main()
