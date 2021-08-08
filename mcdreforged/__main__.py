"""
Entry for MCDR
"""
import sys

from prompt_toolkit.patch_stdout import patch_stdout

from mcdreforged.cli import cli_entry


def main():
	with patch_stdout(raw=True):
		result = cli_entry.entry_point()
	return result


if __name__ == '__main__':
	sys.exit(main())
