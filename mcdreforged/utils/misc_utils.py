"""
Misc tool collection
"""
import inspect
import logging
from typing import Callable, Any


def print_text_to_console(logger: logging.Logger, text: Any):
	from mcdreforged.minecraft.rtext.text import RTextBase
	text_str = RTextBase.from_any(text).to_colored_text()
	if len(text_str) == 0:
		logger.info(text_str)
	else:
		for line in text_str.splitlines():
			logger.info(line)


def copy_signature(target: Callable, origin: Callable) -> Callable:
	"""
	Copy the function signature of origin into target
	"""
	assert callable(target) and callable(origin)

	# https://stackoverflow.com/questions/39926567/python-create-decorator-preserving-function-arguments
	target.__signature__ = inspect.signature(origin)
	return target

