import copy
import unittest
from typing import Any, Dict, Optional, Tuple

from pydantic import ValidationError

from mcdreforged.handler.handler_spec import HandlerSpec
from mcdreforged.handler.impl import SpecServerHandler
from tests.handler import handler_test_utils

MINIMAL: Dict[str, Any] = {
	'name': 'test_handler',
	'control': {'stop': {'command': 'stop'}},
	'parsing': {
		'line': ['(?P<content>.*)'],
		'player_name': '[a-zA-Z0-9_]{3,16}',
	},
}

BASE: Dict[str, Any] = {
	'name': 'base_handler',
	'control': {
		'stop': {'command': 'stop'},
		'send_message': {'builtin': 'minecraft_tellraw'},
		'broadcast_message': {'builtin': 'minecraft_tellraw', 'target': '@a'},
	},
	'parsing': {
		'pre_parse': [{'sub': '^>', 'repl': ''}],
		'line_transforms': [{'builtin': 'strip_minecraft_color'}],
		'line': [r'\[(?P<logging>\w+)] (?P<content>.*)'],
		'player_message': ['<(?P<name>[^>]+)> (?P<message>.*)'],
		'player_name': '[a-zA-Z0-9_]{3,16}',
	},
	'events': {
		'player_joined': [r'(?P<name>\w+) joined'],
		'player_left': [r'(?P<name>\w+) left'],
		'server_stopping': ['Stopping'],
	},
}


def with_value(data: Dict[str, Any], path: Tuple[str, ...], value: Any) -> Dict[str, Any]:
	data = copy.deepcopy(data)
	node = data
	for key in path[:-1]:
		node = node.setdefault(key, {})
	node[path[-1]] = value
	return data


def without(data: Dict[str, Any], path: Tuple[str, ...]) -> Dict[str, Any]:
	data = copy.deepcopy(data)
	node = data
	for key in path[:-1]:
		node = node[key]
	del node[path[-1]]
	return data


class SpecTestCase(unittest.TestCase):
	def assert_invalid(self, data: Dict[str, Any], loc: Optional[Tuple[Any, ...]] = None):
		with self.assertRaises(ValidationError) as ctx:
			HandlerSpec.model_validate(data)
		if loc is not None:
			locs = [e['loc'] for e in ctx.exception.errors()]
			self.assertTrue(any(tuple(l[:len(loc)]) == loc for l in locs), 'expected an error at {}, got {}'.format(loc, locs))


class RequiredFieldsTestCase(SpecTestCase):
	def test_minimal(self):
		HandlerSpec.model_validate(MINIMAL)

	def test_required(self):
		for path in [('name',), ('control',), ('control', 'stop'), ('parsing',), ('parsing', 'line'), ('parsing', 'player_name')]:
			with self.subTest(path=path):
				self.assert_invalid(without(MINIMAL, path), path)

	def test_empty_name(self):
		self.assert_invalid(with_value(MINIMAL, ('name',), ''), ('name',))

	def test_empty_line(self):
		self.assert_invalid(with_value(MINIMAL, ('parsing', 'line'), []), ('parsing', 'line'))

	def test_defaults(self):
		handler = SpecServerHandler(HandlerSpec.model_validate(MINIMAL))
		si = handler_test_utils.server_info('1.21.5')
		self.assertEqual('§a>foo', handler.pre_parse_server_stdout('§a>foo'))
		self.assertEqual('§a<Steve> hi', handler.parse_server_stdout('§a<Steve> hi').content)
		self.assertIsNone(handler.parse_server_stdout('<Steve> hi').player)
		self.assertIsNone(handler.get_send_message_command('Steve', 'hi', si))
		self.assertIsNone(handler.get_broadcast_message_command('hi', si))

		info = handler.parse_server_stdout('Steve joined')
		self.assertIsNone(handler.parse_player_joined(info))
		self.assertIsNone(handler.parse_player_left(info))
		self.assertIsNone(handler.parse_server_version(info))
		self.assertIsNone(handler.parse_server_address(info))
		self.assertFalse(handler.test_server_startup_done(info))
		self.assertFalse(handler.test_rcon_started(info))
		self.assertFalse(handler.test_server_stopping(info))


class RegexValidationTestCase(SpecTestCase):
	def test_invalid_regex(self):
		self.assert_invalid(with_value(MINIMAL, ('parsing', 'line'), ['(?P<content>.*']), ('parsing', 'line', 0))
		self.assert_invalid(with_value(MINIMAL, ('parsing', 'player_name'), '['), ('parsing', 'player_name'))
		self.assert_invalid(with_value(MINIMAL, ('parsing', 'line_transforms'), [{'sub': '(', 'repl': ''}]), ('parsing', 'line_transforms', 0))

	def test_required_groups(self):
		cases = [
			(('parsing', 'line'), ['(?P<message>.*)'], 'content'),
			(('parsing', 'player_message'), ['<(?P<name>[^>]+)> (?P<content>.*)'], 'message'),
			(('parsing', 'player_message'), ['<(?P<player>[^>]+)> (?P<message>.*)'], 'name'),
			(('events', 'player_joined'), ['(?P<player>.+) joined'], 'name'),
			(('events', 'player_left'), ['(.+) left'], 'name'),
			(('events', 'server_version'), ['Version (?P<ver>.+)'], 'version'),
			(('events', 'server_address'), ['(?P<ip>.+)'], 'port'),
			(('events', 'server_address'), ['(?P<port>.+)'], 'ip'),
		]
		for path, patterns, group in cases:
			with self.subTest(path=path, group=group):
				self.assert_invalid(with_value(MINIMAL, path, patterns), (*path, 0))

	def test_groups_ok(self):
		data = with_value(MINIMAL, ('events',), {
			'player_joined': ['(?P<name>.+) joined'],
			'player_left': ['(?P<name>.+) left'],
			'server_version': ['Version (?P<version>.+)'],
			'server_address': ['(?P<ip>.+):(?P<port>\\d+)'],
			'server_startup_done': ['Done'],
			'rcon_started': ['RCON'],
			'server_stopping': ['Stopping'],
		})
		HandlerSpec.model_validate(data)


class TextTransformValidationTestCase(SpecTestCase):
	def test_valid(self):
		HandlerSpec.model_validate(with_value(MINIMAL, ('parsing', 'pre_parse'), [
			{'builtin': 'strip_ansi_color'},
			{'builtin': 'strip_minecraft_color'},
			{'sub': 'a', 'repl': 'b'},
			{'sub': 'a', 'repl': 'b', 'count': 1},
		]))

	def test_invalid(self):
		for transform in [
			{'builtin': 'no_such_builtin'},
			{'sub': 'a'},
			{'repl': 'b'},
			{'sub': 'a', 'repl': 'b', 'count': -1},
		]:
			with self.subTest(transform=transform):
				self.assert_invalid(with_value(MINIMAL, ('parsing', 'pre_parse'), [transform]), ('parsing', 'pre_parse', 0))


class StopMethodValidationTestCase(SpecTestCase):
	def test_valid(self):
		for stop in [
			{'command': 'stop'},
			{'signal': 'SIGTERM'},
			{'signal': 'CTRL_BREAK_EVENT'},
			{'signal': 15},
			{'signal': 'SIGINT', 'scope': 'process'},
			{'signal': 'SIGINT', 'scope': 'process_tree'},
		]:
			with self.subTest(stop=stop):
				HandlerSpec.model_validate(with_value(MINIMAL, ('control', 'stop'), stop))

	def test_invalid(self):
		for stop in [
			{'command': 'stop', 'signal': 'SIGTERM'},
			{'signal': 'TERM'},
			{'signal': -1},
			{'signal': 'SIGTERM', 'scope': 'everything'},
			{'command': 'stop', 'scope': 'process'},
			{},
		]:
			with self.subTest(stop=stop):
				self.assert_invalid(with_value(MINIMAL, ('control', 'stop'), stop), ('control', 'stop'))


class MessageMethodValidationTestCase(SpecTestCase):
	def test_valid(self):
		for key, method in [
			('send_message', {'builtin': 'minecraft_tellraw'}),
			('send_message', {'template': 'tell {target} {message}', 'message_format': 'plain'}),
			('send_message', {'template': '{{literal}} {message}', 'message_format': 'json'}),
			('send_message', None),
			('broadcast_message', {'builtin': 'minecraft_tellraw', 'target': '@a'}),
			('broadcast_message', {'template': 'say {message}', 'message_format': 'plain'}),
			('broadcast_message', None),
		]:
			with self.subTest(key=key, method=method):
				HandlerSpec.model_validate(with_value(MINIMAL, ('control', key), method))

	def test_invalid(self):
		for key, method in [
			('send_message', {'builtin': 'no_such_builtin'}),
			('send_message', {'template': 'tell {player} {message}', 'message_format': 'plain'}),
			('send_message', {'template': 'tell {target} {message!r}', 'message_format': 'plain'}),
			('send_message', {'template': 'tell {target} {message:>10}', 'message_format': 'plain'}),
			('send_message', {'template': 'tell {target} {message.x}', 'message_format': 'plain'}),
			('send_message', {'template': 'tell {target} {message', 'message_format': 'plain'}),
			('send_message', {'template': 'tell {target} {message}'}),
			('send_message', {'template': 'tell {target} {message}', 'message_format': 'xml'}),
			('broadcast_message', {'template': 'tell {target} {message}', 'message_format': 'plain'}),
			('broadcast_message', {'builtin': 'minecraft_tellraw'}),
			('broadcast_message', {'builtin': 'minecraft_tellraw', 'target': ''}),
		]:
			with self.subTest(key=key, method=method):
				self.assert_invalid(with_value(MINIMAL, ('control', key), method), ('control', key))


class UnknownFieldTestCase(SpecTestCase):
	def test_unknown_fields_ignored(self):
		data = copy.deepcopy(MINIMAL)
		data['future_field'] = 1
		data['control']['future_field'] = 1
		data['parsing']['future_field'] = 1
		data['events'] = {'future_event': ['foo']}
		HandlerSpec.model_validate(data)


class ExtendTestCase(SpecTestCase):
	def setUp(self):
		self.base = HandlerSpec.model_validate(BASE)

	def extend(self, override: Dict[str, Any]) -> SpecServerHandler:
		return SpecServerHandler(self.base.extend({'name': 'child_handler', **override}))

	def test_inherit_all(self):
		handler = self.extend({})
		self.assertEqual('child_handler', handler.get_name())
		self.assertEqual('stop', handler.get_stop_command())
		self.assertEqual('foo', handler.pre_parse_server_stdout('>foo'))
		info = handler.parse_server_stdout('[INFO] §a<Steve> hi')
		self.assertEqual('Steve', info.player)
		self.assertEqual('Steve', handler.parse_player_joined(handler.parse_server_stdout('[INFO] Steve joined')))
		self.assertEqual('tellraw @a "hi"', handler.get_broadcast_message_command('hi', handler_test_utils.server_info(None)))

	def test_name_not_inherited(self):
		with self.assertRaises(ValidationError):
			self.base.extend({})

	def test_extends_key_ignored(self):
		handler = SpecServerHandler(self.base.extend({'name': 'child_handler', 'extends': 'base_handler'}))
		self.assertEqual('child_handler', handler.get_name())

	def test_object_merged_by_key(self):
		handler = self.extend({'parsing': {'player_name': r'\.?[a-zA-Z0-9_]{3,16}'}})
		info = handler.parse_server_stdout('[INFO] §a<.Steve> hi')
		self.assertEqual('.Steve', info.player)  # line, line_transforms and player_message inherited
		self.assertEqual('foo', handler.pre_parse_server_stdout('>foo'))

		handler = self.extend({'events': {'player_left': [r'(?P<name>\w+) quit']}})
		self.assertEqual('Steve', handler.parse_player_joined(handler.parse_server_stdout('[INFO] Steve joined')))
		self.assertEqual('Steve', handler.parse_player_left(handler.parse_server_stdout('[INFO] Steve quit')))
		self.assertIsNone(handler.parse_player_left(handler.parse_server_stdout('[INFO] Steve left')))

	def test_list_replaced(self):
		handler = self.extend({'parsing': {'player_message': [r'\[(?P<name>\w+)] (?P<message>.*)']}})
		self.assertEqual('Steve', handler.parse_server_stdout('[INFO] [Steve] hi').player)
		self.assertIsNone(handler.parse_server_stdout('[INFO] <Steve> hi').player)

	def test_empty_list_clears(self):
		handler = self.extend({'parsing': {'pre_parse': [], 'line_transforms': []}, 'events': {'server_stopping': []}})
		self.assertEqual('>foo', handler.pre_parse_server_stdout('>foo'))
		self.assertEqual('§ahi', handler.parse_server_stdout('[INFO] §ahi').content)
		self.assertFalse(handler.test_server_stopping(handler.parse_server_stdout('[INFO] Stopping')))

	def test_empty_line_invalid(self):
		with self.assertRaises(ValidationError):
			self.extend({'parsing': {'line': []}})

	def test_union_replaced(self):
		spec = self.base.extend({'name': 'child_handler', 'control': {'stop': {'signal': 'SIGTERM'}}})
		self.assertRaises(Exception, SpecServerHandler(spec).get_stop_command)

		handler = self.extend({'control': {'broadcast_message': {'template': 'say {message}', 'message_format': 'plain'}}})
		self.assertEqual('say hi', handler.get_broadcast_message_command('hi', handler_test_utils.server_info(None)))

	def test_null_disables(self):
		handler = self.extend({'control': {'send_message': None}})
		si = handler_test_utils.server_info(None)
		self.assertIsNone(handler.get_send_message_command('Steve', 'hi', si))
		self.assertEqual('tellraw @a "hi"', handler.get_broadcast_message_command('hi', si))

	def test_result_validated(self):
		with self.assertRaises(ValidationError):
			self.extend({'parsing': {'line': ['(?P<message>.*)']}})
		with self.assertRaises(ValidationError):
			self.extend({'control': {'stop': {'command': 'stop', 'signal': 'SIGTERM'}}})

	def test_base_unchanged(self):
		self.extend({'parsing': {'player_message': []}, 'control': {'send_message': None}})
		handler = SpecServerHandler(self.base)
		self.assertEqual('Steve', handler.parse_server_stdout('[INFO] <Steve> hi').player)
		self.assertEqual('tellraw Steve "hi"', handler.get_send_message_command('Steve', 'hi', handler_test_utils.server_info(None)))


if __name__ == '__main__':
	unittest.main()
