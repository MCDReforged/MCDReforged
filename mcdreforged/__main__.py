"""
Entry for MCDR
"""
import sys

from prompt_toolkit.patch_stdout import patch_stdout

from mcdreforged.cli import cli_entry


def main():
	with patch_stdout(raw=True):
		return cli_entry.entry_point()


if __name__ == '__main__':
	sys.exit(main())
