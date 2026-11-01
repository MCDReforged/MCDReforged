import unittest
from typing import Any, Dict

from mcdreforged.handler.handler_spec import HandlerSpec
from mcdreforged.handler.impl import SpecServerHandler
from mcdreforged.minecraft.rtext.style import RColor
from mcdreforged.minecraft.rtext.text import RText
from tests.handler import handler_test_utils


def make_handler(**overrides: Any) -> SpecServerHandler:
	data: Dict[str, Any] = {
		'name': 'test_handler',
		'control': {'stop': {'command': 'stop'}},
		'parsing': {
			'line': [r'\[(?P<hour>\d+):(?P<min>\d+):(?P<sec>\d+) (?P<logging>\w+)] (?P<content>.*)'],
			'player_message': ['<(?P<name>[^>]+)> (?P<message>.*)'],
			'player_name': '[a-zA-Z0-9_]{3,16}',
		},
	}
	for key, value in overrides.items():
		if key in ('control', 'parsing'):
			data[key] = {**data[key], **value}
		else:
			data[key] = value
	return SpecServerHandler(HandlerSpec.model_validate(data))


class LineParsingTestCase(unittest.TestCase):
	def test_fields(self):
		handler = make_handler()
		info = handler.parse_server_stdout('[09:08:07 INFO] hello world')
		self.assertEqual((9, 8, 7), (info.hour, info.min, info.sec))
		self.assertEqual('INFO', info.logging_level)
		self.assertEqual('hello world', info.content)
		self.assertEqual('[09:08:07 INFO] hello world', info.raw_content)
		self.assertTrue(info.is_from_server)
		self.assertIsNone(info.player)

	def test_fullmatch(self):
		handler = make_handler(parsing={'line': ['foo (?P<content>bar)']})
		self.assertEqual('bar', handler.parse_server_stdout('foo bar').content)
		self.assertRaises(Exception, handler.parse_server_stdout, 'foo bar baz')
		self.assertRaises(Exception, handler.parse_server_stdout, 'xfoo bar')

	def test_unmatched_line_raises(self):
		handler = make_handler()
		self.assertRaises(Exception, handler.parse_server_stdout, 'not a log line')

	def test_first_matching_rule_wins(self):
		handler = make_handler(parsing={'line': [
			r'A (?P<content>.*)',
			r'(?P<logging>\w+) (?P<content>.*)',
		]})
		info = handler.parse_server_stdout('A hello')
		self.assertEqual('hello', info.content)
		self.assertIsNone(info.logging_level)

		info = handler.parse_server_stdout('B hello')
		self.assertEqual('hello', info.content)
		self.assertEqual('B', info.logging_level)

	def test_optional_groups(self):
		handler = make_handler(parsing={'line': ['(?P<content>.*)']})
		info = handler.parse_server_stdout('hello')
		self.assertEqual('hello', info.content)
		self.assertIsNone(info.hour)
		self.assertIsNone(info.min)
		self.assertIsNone(info.sec)
		self.assertIsNone(info.logging_level)

		handler = make_handler(parsing={'line': [r'((?P<hour>\d+) )?(?P<content>.*)']})
		self.assertIsNone(handler.parse_server_stdout('hello').hour)
		self.assertEqual(12, handler.parse_server_stdout('12 hello').hour)

	def test_other_groups_ignored(self):
		handler = make_handler(parsing={'line': [r'(\d+) (?P<thread>\w+) (?P<content>.*)']})
		info = handler.parse_server_stdout('123 main hello')
		self.assertEqual('hello', info.content)
		self.assertIsNone(info.hour)
		self.assertIsNone(info.logging_level)

	def test_console_command(self):
		info = make_handler().parse_console_command('!!MCDR status')
		self.assertTrue(info.is_from_console)
		self.assertEqual('!!MCDR status', info.content)
		self.assertEqual('!!MCDR status', info.raw_content)


class TextTransformTestCase(unittest.TestCase):
	def test_pre_parse(self):
		handler = make_handler(parsing={
			'pre_parse': [{'sub': '^#+', 'repl': '', 'count': 1}],
			'line': ['(?P<content>.*)'],
		})
		text = handler.pre_parse_server_stdout('##hello #world')
		self.assertEqual('hello #world', text)
		info = handler.parse_server_stdout(text)
		self.assertEqual('hello #world', info.raw_content)
		self.assertEqual('hello #world', info.content)

	def test_pre_parse_default_unchanged(self):
		handler = make_handler()
		for text in ['\033[33mfoo\033[0m', '§afoo', '>\rfoo']:
			self.assertEqual(text, handler.pre_parse_server_stdout(text))

	def test_line_transforms_affect_content_only(self):
		handler = make_handler(parsing={
			'line_transforms': [{'builtin': 'strip_ansi_color'}, {'builtin': 'strip_minecraft_color'}],
			'line': ['(?P<content>.*)'],
		})
		text = '\033[33m§eSteve§r joined\033[0m'
		self.assertEqual(text, handler.pre_parse_server_stdout(text))
		info = handler.parse_server_stdout(text)
		self.assertEqual('Steve joined', info.content)
		self.assertEqual(text, info.raw_content)

	def test_line_transforms_apply_before_line_matching(self):
		handler = make_handler(parsing={
			'line_transforms': [{'builtin': 'strip_minecraft_color'}],
			'line': ['A (?P<content>.*)'],
		})
		self.assertEqual('hello', handler.parse_server_stdout('§aA §bhello').content)

	def test_transforms_run_in_order(self):
		handler = make_handler(parsing={
			'line_transforms': [
				{'sub': 'a', 'repl': 'b'},
				{'sub': 'b', 'repl': 'c'},
			],
			'line': ['(?P<content>.*)'],
		})
		self.assertEqual('ccc', handler.parse_server_stdout('abc').content)

	def test_sub_count(self):
		def handler_with_count(count: int) -> SpecServerHandler:
			return make_handler(parsing={
				'line_transforms': [{'sub': 'x', 'repl': '-', 'count': count}],
				'line': ['(?P<content>.*)'],
			})
		self.assertEqual('-xx', handler_with_count(1).parse_server_stdout('xxx').content)
		self.assertEqual('---', handler_with_count(0).parse_server_stdout('xxx').content)

	def test_sub_group_reference(self):
		handler = make_handler(parsing={
			'line_transforms': [{'sub': r'(\w+)@(\w+)', 'repl': r'\2.\1'}],
			'line': ['(?P<content>.*)'],
		})
		self.assertEqual('b.a', handler.parse_server_stdout('a@b').content)


class PlayerMessageTestCase(unittest.TestCase):
	def test_player_message(self):
		info = make_handler().parse_server_stdout('[09:08:07 INFO] <Steve> !!MCDR')
		self.assertEqual('Steve', info.player)
		self.assertEqual('!!MCDR', info.content)
		self.assertEqual('[09:08:07 INFO] <Steve> !!MCDR', info.raw_content)

	def test_no_player_message_rules(self):
		handler = make_handler(parsing={'player_message': []})
		info = handler.parse_server_stdout('[09:08:07 INFO] <Steve> hi')
		self.assertIsNone(info.player)
		self.assertEqual('<Steve> hi', info.content)

	def test_invalid_name_tries_next_rule(self):
		handler = make_handler(parsing={'player_message': [
			'<(?P<name>[^>]+)> (?P<message>.*)',
			r'<\[\w+](?P<name>[^>]+)> (?P<message>.*)',
		]})
		info = handler.parse_server_stdout('[09:08:07 INFO] <[Builder]Steve> hi')
		self.assertEqual('Steve', info.player)
		self.assertEqual('hi', info.content)

	def test_invalid_name_not_a_player(self):
		info = make_handler().parse_server_stdout('[09:08:07 INFO] <S> hi')
		self.assertIsNone(info.player)
		self.assertEqual('<S> hi', info.content)

	def test_player_name(self):
		handler = make_handler(parsing={'player_name': r'\.?[a-zA-Z0-9_]{3,16}'})
		self.assertTrue(handler.validate_player_name('.Steve'))
		self.assertTrue(handler.validate_player_name('Steve'))
		self.assertFalse(handler.validate_player_name('Steve!'))  # fullmatch
		self.assertEqual('.Steve', handler.parse_server_stdout('[09:08:07 INFO] <.Steve> hi').player)


class EventTestCase(unittest.TestCase):
	EVENTS = {
		'player_joined': ['(?P<name>\\w+) joined'],
		'player_left': ['(?P<name>\\w+) left'],
		'server_version': ['Version (?P<version>.+)'],
		'server_address': ['Address (?P<ip>\\S+):(?P<port>\\d+)'],
		'server_startup_done': ['Done'],
		'rcon_started': ['RCON'],
		'server_stopping': ['Stopping'],
	}

	def setUp(self):
		self.handler = make_handler(events=self.EVENTS)

	def parse(self, content: str):
		return self.handler.parse_server_stdout('[09:08:07 INFO] ' + content)

	def test_events(self):
		self.assertEqual('Steve', self.handler.parse_player_joined(self.parse('Steve joined')))
		self.assertEqual('Steve', self.handler.parse_player_left(self.parse('Steve left')))
		self.assertEqual('1.21.5', self.handler.parse_server_version(self.parse('Version 1.21.5')))
		self.assertEqual(('0.0.0.0', 25565), self.handler.parse_server_address(self.parse('Address 0.0.0.0:25565')))
		self.assertTrue(self.handler.test_server_startup_done(self.parse('Done')))
		self.assertTrue(self.handler.test_rcon_started(self.parse('RCON')))
		self.assertTrue(self.handler.test_server_stopping(self.parse('Stopping')))

	def assert_no_event(self, info):
		self.assertIsNone(self.handler.parse_player_joined(info))
		self.assertIsNone(self.handler.parse_player_left(info))
		self.assertIsNone(self.handler.parse_server_version(info))
		self.assertIsNone(self.handler.parse_server_address(info))
		self.assertFalse(self.handler.test_server_startup_done(info))
		self.assertFalse(self.handler.test_rcon_started(info))
		self.assertFalse(self.handler.test_server_stopping(info))

	def test_fullmatch(self):
		for content in ['Steve joined!', 'Version', 'Address 0.0.0.0', 'Done!', 'xRCON', 'Stopping server']:
			self.assert_no_event(self.parse(content))

	def test_player_message_is_not_event(self):
		for content in ['Steve joined', 'Steve left', 'Version 1.21.5', 'Address 0.0.0.0:25565', 'Done', 'RCON', 'Stopping']:
			info = self.parse('<Alex> ' + content)
			self.assertEqual('Alex', info.player)
			self.assert_no_event(info)

	def test_console_input_is_not_event(self):
		for content in ['Steve joined', 'Done', 'Stopping']:
			self.assert_no_event(self.handler.parse_console_command(content))

	def test_event_player_name_validated(self):
		self.assertIsNone(self.handler.parse_player_joined(self.parse('S joined')))
		self.assertIsNone(self.handler.parse_player_left(self.parse('S left')))

	def test_event_invalid_name_tries_next_rule(self):
		handler = make_handler(events={'player_left': [
			r'(?P<name>\S+) left',
			r'\[\w+](?P<name>\S+) left',
		]})
		info = handler.parse_server_stdout('[09:08:07 INFO] [Builder]Steve left')
		self.assertEqual('Steve', handler.parse_player_left(info))

	def test_first_matching_rule_wins(self):
		handler = make_handler(events={'server_version': [
			'Version (?P<version>.+)',
			'Version (?P<version>\\d+)',
		]})
		info = handler.parse_server_stdout('[09:08:07 INFO] Version 1.2')
		self.assertEqual('1.2', handler.parse_server_version(info))

	def test_no_event_rules(self):
		self.handler = make_handler()
		for content in ['Steve joined', 'Version 1.21.5', 'Address 0.0.0.0:25565', 'Done', 'RCON', 'Stopping']:
			self.assert_no_event(self.parse(content))


class ValidatePlayerNameOverrideTestCase(unittest.TestCase):
	class AllowAllHandler(SpecServerHandler):
		def validate_player_name(self, name: str) -> bool:
			return True

	def test_override_used_by_player_message_and_events(self):
		base = make_handler(events={'player_joined': [r'(?P<name>.+) joined'], 'player_left': [r'(?P<name>.+) left']})
		handler = self.AllowAllHandler(base.spec)

		info = handler.parse_server_stdout('[09:08:07 INFO] <A B> hi')
		self.assertEqual('A B', info.player)
		self.assertEqual('hi', info.content)

		info = handler.parse_server_stdout('[09:08:07 INFO] A B joined')
		self.assertEqual('A B', handler.parse_player_joined(info))
		info = handler.parse_server_stdout('[09:08:07 INFO] A B left')
		self.assertEqual('A B', handler.parse_player_left(info))


class ControlTestCase(unittest.TestCase):
	def test_stop_command(self):
		self.assertEqual('end', make_handler(control={'stop': {'command': 'end'}}).get_stop_command())

	def test_message_disabled(self):
		handler = make_handler()
		si = handler_test_utils.server_info('1.21.5')
		self.assertIsNone(handler.get_send_message_command('Steve', 'hi', si))
		self.assertIsNone(handler.get_broadcast_message_command('hi', si))

	def test_minecraft_tellraw(self):
		handler = make_handler(control={
			'send_message': {'builtin': 'minecraft_tellraw'},
			'broadcast_message': {'builtin': 'minecraft_tellraw', 'target': '@a[tag=foo]'},
		})
		si = handler_test_utils.server_info('1.12.2')
		self.assertEqual('tellraw Steve "hi"', handler.get_send_message_command('Steve', 'hi', si))
		self.assertEqual('tellraw @a[tag=foo] "hi"', handler.get_broadcast_message_command('hi', si))

	def test_template_json(self):
		handler = make_handler(control={
			'send_message': {'template': 'msg {target} {message}', 'message_format': 'json'},
			'broadcast_message': {'template': 'alertraw {message}', 'message_format': 'json'},
		})
		si = handler_test_utils.server_info(None)
		self.assertEqual('msg Steve ' + handler_test_utils.STR_MESSAGE_JSON, handler.get_send_message_command('Steve', handler_test_utils.STR_MESSAGE, si))
		self.assertEqual('alertraw ' + handler_test_utils.STR_MESSAGE_JSON, handler.get_broadcast_message_command(handler_test_utils.STR_MESSAGE, si))
		self.assertEqual('alertraw ' + handler_test_utils.RTEXT_MESSAGE_JSON, handler.get_broadcast_message_command(handler_test_utils.RTEXT_MESSAGE, si))

	def test_template_json_follows_server_version(self):
		handler = make_handler(control={'broadcast_message': {'template': 'alertraw {message}', 'message_format': 'json'}})
		message = handler_test_utils.RTEXT_EVENT_MESSAGE
		self.assertEqual('alertraw ' + handler_test_utils.RTEXT_EVENT_MESSAGE_JSON_LEGACY, handler.get_broadcast_message_command(message, handler_test_utils.server_info('1.21.4')))
		self.assertEqual('alertraw ' + handler_test_utils.RTEXT_EVENT_MESSAGE_JSON_1_21_5, handler.get_broadcast_message_command(message, handler_test_utils.server_info('1.21.5')))

	def test_template_plain(self):
		handler = make_handler(control={
			'send_message': {'template': 'tell {target} {message}', 'message_format': 'plain'},
			'broadcast_message': {'template': 'say {message}', 'message_format': 'plain'},
		})
		si = handler_test_utils.server_info(None)
		self.assertEqual('tell Steve hi "there" x', handler.get_send_message_command('Steve', handler_test_utils.STR_MESSAGE, si))
		self.assertEqual('say hi', handler.get_broadcast_message_command(RText('§ahi', color=RColor.red), si))

	def test_template_literal_braces(self):
		handler = make_handler(control={'broadcast_message': {'template': 'say {{{message}}}', 'message_format': 'plain'}})
		self.assertEqual('say {hi}', handler.get_broadcast_message_command('hi', handler_test_utils.server_info(None)))


if __name__ == '__main__':
	unittest.main()
