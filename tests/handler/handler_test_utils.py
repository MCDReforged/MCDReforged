import unittest
from typing import Optional

from mcdreforged.handler.server_handler import ServerHandler
from mcdreforged.info_reactor.server_information import ServerInformation
from mcdreforged.minecraft.rtext.click_event import RAction
from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText

STR_MESSAGE = 'hi "there" §ax'
RTEXT_MESSAGE = RText('hi', color=RColor.red)
RTEXT_EVENT_MESSAGE = RText('hi').c(RAction.run_command, '/help').h('tip')

STR_MESSAGE_JSON = r'"hi \"there\" §ax"'
RTEXT_MESSAGE_JSON = '{"text":"hi","color":"red"}'
RTEXT_EVENT_MESSAGE_JSON_LEGACY = '{"text":"hi","clickEvent":{"action":"run_command","value":"/help"},"hoverEvent":{"action":"show_text","value":{"text":"tip"}}}'
RTEXT_EVENT_MESSAGE_JSON_1_21_5 = '{"text":"hi","click_event":{"action":"run_command","command":"/help"},"hover_event":{"action":"show_text","value":{"text":"tip"}}}'


def server_info(version: Optional[str]) -> ServerInformation:
	info = ServerInformation()
	info.version = version
	return info


def assert_minecraft_tellraw_commands(tc: unittest.TestCase, handler: ServerHandler):
	for version, prefix in [(None, ''), ('1.12.2', ''), ('1.13', 'execute at @p run '), ('1.21.5', 'execute at @p run ')]:
		si = server_info(version)
		tc.assertEqual(prefix + 'tellraw Steve ' + STR_MESSAGE_JSON, handler.get_send_message_command('Steve', STR_MESSAGE, si), version)
		tc.assertEqual(prefix + 'tellraw @a ' + STR_MESSAGE_JSON, handler.get_broadcast_message_command(STR_MESSAGE, si), version)
		tc.assertEqual(prefix + 'tellraw Steve ' + RTEXT_MESSAGE_JSON, handler.get_send_message_command('Steve', RTEXT_MESSAGE, si), version)
		tc.assertEqual(prefix + 'tellraw @a ' + RTEXT_MESSAGE_JSON, handler.get_broadcast_message_command(RTEXT_MESSAGE, si), version)

	prefix = 'execute at @p run tellraw Steve '
	tc.assertEqual(prefix + RTEXT_EVENT_MESSAGE_JSON_LEGACY, handler.get_send_message_command('Steve', RTEXT_EVENT_MESSAGE, server_info('1.21.4')))
	tc.assertEqual(prefix + RTEXT_EVENT_MESSAGE_JSON_1_21_5, handler.get_send_message_command('Steve', RTEXT_EVENT_MESSAGE, server_info('1.21.5')))


def assert_alertraw_broadcast_only(tc: unittest.TestCase, handler: ServerHandler):
	si = server_info(None)
	tc.assertIsNone(handler.get_send_message_command('Steve', STR_MESSAGE, si))
	tc.assertEqual('alertraw ' + STR_MESSAGE_JSON, handler.get_broadcast_message_command(STR_MESSAGE, si))
	tc.assertEqual('alertraw ' + RTEXT_MESSAGE_JSON, handler.get_broadcast_message_command(RTEXT_MESSAGE, si))
	tc.assertEqual('alertraw ' + RTEXT_EVENT_MESSAGE_JSON_1_21_5, handler.get_broadcast_message_command(RTEXT_EVENT_MESSAGE, server_info('1.21.5')))


def assert_jline_prompt_stripped(tc: unittest.TestCase, handler: ServerHandler):
	tc.assertEqual('02:06:38 [INFO] foo', handler.pre_parse_server_stdout('>\r02:06:38 [INFO] foo'))
	tc.assertEqual('foo', handler.pre_parse_server_stdout('>>>\rfoo'))
	tc.assertEqual('>\rfoo', handler.pre_parse_server_stdout('>\r>\rfoo'))  # only the first prompt
	tc.assertEqual('foo >\r', handler.pre_parse_server_stdout('foo >\r'))  # only at line start
	tc.assertEqual('foo', handler.pre_parse_server_stdout('foo'))


def assert_pre_parse_unchanged(tc: unittest.TestCase, handler: ServerHandler):
	for text in ['>\r02:06:38 [INFO] foo', '\033[33mfoo\033[0m', '§afoo', 'foo']:
		tc.assertEqual(text, handler.pre_parse_server_stdout(text))
