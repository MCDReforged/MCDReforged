import json
import re

from mcdreforged import constant


def remove_suffix(text: str, suffix: str):
	pos = text.rfind(suffix)
	return text[:pos] if pos >= 0 else text


def clean_minecraft_color_code(text):
	return re.sub('§[a-z0-9]', '', str(text))


def clean_console_color_code(text):
	return re.sub(r'\033\[(\d+(;\d+)?)?m', '', text)


def format_plugin_file_path(file_path):
	file_path = remove_suffix(file_path, constant.DISABLED_PLUGIN_FILE_SUFFIX)
	file_path = remove_suffix(file_path, constant.PLUGIN_FILE_SUFFIX)
	file_path += constant.PLUGIN_FILE_SUFFIX
	return file_path


def format_plugin_file_path_disabled(file_path):
	return format_plugin_file_path(file_path) + constant.DISABLED_PLUGIN_FILE_SUFFIX


def hump_to_underline(name: str) -> str:
	return re.sub(r'([a-z]|\d)([A-Z])', r'\1_\2', name).lower()


def auto_quotes(text: str):
	if not isinstance(text, str):
		raise TypeError('Parameter text should be a str, but {} founded'.format(type(text)))
	if ' ' in text:
		return json.dumps(text)
	else:
		return text
