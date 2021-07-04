"""
Entry for MCDR
"""
import sys

from mcdreforged.cli import cli_entry


def main():
	return cli_entry.entry_point()


if __name__ == '__main__':
	sys.exit(main())
