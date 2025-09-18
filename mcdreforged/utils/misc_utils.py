"""
Misc tool collection
"""
import inspect
import logging
import os
from typing import Callable, Any, Optional, Dict, List, Union, TypeVar

from pydantic import BaseModel


def print_text_to_console(logger: logging.Logger, text: Any):
	from mcdreforged.minecraft.rtext.text import RTextBase
	text_str = RTextBase.from_any(text).to_colored_text()
	if len(text_str) == 0:
		logger.info(text_str)
	else:
		for line in text_str.splitlines():
			logger.info(line)


_F = TypeVar('_F', bound=Callable)


def copy_signature(target: _F, origin: Callable) -> _F:
	"""
	Copy the function signature of origin into target
	"""
	assert callable(target) and callable(origin)

	# https://stackoverflow.com/questions/39926567/python-create-decorator-preserving-function-arguments
	target.__signature__ = inspect.signature(origin)  # type: ignore
	return target


def prepare_subprocess_environment(envs: Optional[Union[List[str], Dict[str, str]]], inherit: bool) -> Optional[Dict[str, str]]:
	if envs is None and inherit:
		return None

	result: Dict[str, str] = {}
	if inherit:
		result.update(os.environ)

	if envs is None:
		pass
	elif isinstance(envs, dict):
		result.update(envs)
	elif isinstance(envs, list):
		for kv_pair in envs:
			parts = kv_pair.split('=', 1)
			if len(parts) == 2:
				result[parts[0]] = parts[1]
	else:
		raise TypeError('envs must be a dict or a list, got {}'.format(type(envs)))

	return result


def contains_unset_default_fields(obj: BaseModel) -> bool:
	for field_name in type(obj).model_fields:
		if field_name not in obj.model_fields_set:
			return True

		field_value = getattr(obj, field_name, None)
		if isinstance(field_value, BaseModel):
			if contains_unset_default_fields(field_value):
				return True
		elif isinstance(field_value, (list, tuple, set)):
			for item in field_value:
				if isinstance(item, BaseModel) and contains_unset_default_fields(item):
					return True
		elif isinstance(field_value, dict):
			for item in field_value.values():
				if isinstance(item, BaseModel) and contains_unset_default_fields(item):
					return True

	return False
