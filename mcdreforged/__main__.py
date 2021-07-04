"""
Entry for MCDR
"""
import sys

from mcdreforged.cli import cli_handler


def main():
	return cli_handler.entry_point()


if __name__ == '__main__':
	sys.exit(main())
