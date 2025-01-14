import unittest
from abc import ABC
from enum import Enum
from typing import Type, Any, TypeVar, Set

from typing_extensions import override

from mcdreforged.api.command import *
from mcdreforged.api.types import CommandSource
from mcdreforged.command.builder.callback import CallbackError, DirectCallbackInvoker
from mcdreforged.command.builder.nodes.special import CountingLiteral
from mcdreforged.utils.types.message import MessageText

_T = TypeVar('_T')


class _TestCommandSource(CommandSource):
	@override
	def get_server(self):
		raise RuntimeError()

	@override
	def get_permission_level(self) -> int:
		raise RuntimeError()

	@override
	def reply(self, message: MessageText, **kwargs) -> None:
		raise RuntimeError()


class CommandTestCase(ABC, unittest.TestCase):
	# -------------
	#   callbacks
	# -------------

	def callback_hit(self, source: CommandSource, ctx: dict):
		self.has_hit = True

	def callback_dummy(self, source: CommandSource, ctx: dict):
		pass

	def set_result_from_ctx(self, ctx: dict, key: str):
		self.result = ctx[key]

	def set_result(self, result: Any):
		self.result = result

	# ---------
	#   utils
	# ---------

	def run_command(self, executor: Literal, command: str):
		self.has_hit = False
		self.result = None
		# noinspection PyTypeChecker
		executions = executor._entry_execute(None, command)
		for execution in executions:
			execution.scheduled_callback.invoke(DirectCallbackInvoker())

	def check_hit(self, value: bool):
		self.assertEqual(self.has_hit, value)

	def check_result(self, result):
		self.assertEqual(type(self.result), type(result))
		self.assertEqual(self.result, result)

	def cast(self, typ: Type[_T], obj: Any) -> _T:
		self.assertIsInstance(obj, typ)
		return obj

	def run_command_and_check_result(self, executor: Literal, command: str, result):
		self.run_command(executor, command)
		self.check_result(result)

	def run_command_and_check_hit(self, executor: Literal, command: str, value: bool):
		self.run_command(executor, command)
		self.check_hit(value)

	def assert_raises_and_check_hit(self, value: bool, error: Type[Exception], func, *args, **kwargs):
		self.assertRaises(error, func, *args, **kwargs)
		self.check_hit(value)


class CommandTreeTestCase(CommandTestCase):

	# ---------
	#   Tests
	# ---------

	# noinspection PyUnresolvedReferences
	def test_1_tree(self):
		executor = Literal('test').\
			then(Text('a')).\
			then(Number('b')).\
			then(Literal('c')).\
			then(Literal('d'))
		children = executor.get_children()

		# Literal nodes goes first, then argument nodes
		self.assertEqual(4, len(children))
		self.assertIsInstance(children[0], Literal)
		self.assertIsInstance(children[1], Literal)
		self.assertIsInstance(children[2], Text)
		self.assertIsInstance(children[3], Number)
		self.assertEqual({'c'}, children[0].literals)
		self.assertEqual({'d'}, children[1].literals)
		self.assertEqual('a', children[2].get_name())
		self.assertEqual('b', children[3].get_name())

	def test_2_literal(self):
		executor = Literal('test').runs(self.callback_hit)
		self.assertRaises(UnknownArgument, self.run_command, executor, 'awa')
		self.check_hit(False)
		self.run_command_and_check_hit(executor, 'test', True)
		self.assertRaises(UnknownArgument, self.run_command, executor, 'another')

		executor = Literal('test').then(Literal('ping').runs(self.callback_dummy)).then(Literal('pong').runs(self.callback_hit))
		self.run_command_and_check_hit(executor, 'test ping', False)
		self.run_command_and_check_hit(executor, 'test pong', True)
		self.run_command_and_check_hit(executor, 'test    pong', True)

		self.assertRaises(UnknownCommand, self.run_command, executor, 'test')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test pingpong')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test ping extra')

		executor = Literal('test').then(Literal(['ping1', 'ping2']).runs(self.callback_hit))
		self.run_command_and_check_hit(executor, 'test ping1', True)
		self.run_command_and_check_hit(executor, 'test ping2', True)

		self.assertRaises(TypeError, Literal, 'ab cd')
		self.assertRaises(TypeError, Literal, 123)
		self.assertRaises(TypeError, Literal, ['ab', 'c '])

		executor = Literal('test').then(Literal('a')).then(Literal('a').then(Literal('b').runs(self.callback_hit)))
		self.run_command_and_check_hit(executor, 'test a b', True)

	def test_3_int(self):
		executor = Literal('int').then(Integer('i').runs(lambda s, ctx: self.set_result_from_ctx(ctx, 'i')))
		self.run_command_and_check_result(executor, 'int 10', 10)
		self.run_command_and_check_result(executor, 'int -121', -121)
		self.assertRaises(InvalidInteger, self.run_command, executor, 'int 1.0')
		self.assertRaises(InvalidInteger, self.run_command, executor, 'int xxx')
		self.assertRaises(InvalidInteger, self.run_command, executor, 'int 123abc')

	def test_4_int_range(self):
		executor = Literal('int2').then(Integer('i').in_range(10, 20).runs(lambda s, ctx: self.set_result_from_ctx(ctx, 'i')))
		self.run_command_and_check_result(executor, 'int2 10', 10)
		self.run_command_and_check_result(executor, 'int2 20', 20)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'int2 9')
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'int2 21')

	def test_5_float(self):
		executor = Literal('float').then(Float('f').in_range(-10, 20).runs(lambda s, ctx: self.set_result_from_ctx(ctx, 'f')))
		self.run_command_and_check_result(executor, 'float 12.34', 12.34)
		self.run_command_and_check_result(executor, 'float -10.0', -10.0)
		self.run_command_and_check_result(executor, 'float 1e1', 1e1)
		self.run_command_and_check_result(executor, 'float -1.56e-9', -1.56e-9)
		self.run_command_and_check_result(executor, 'float .8', .8)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'float 1.2e9')
		self.assertRaises(InvalidFloat, self.run_command, executor, 'float 1.2.3')

	def test_6_number(self):
		executor = Literal('number').then(Number('n').in_range(-10, 20).runs(lambda s, ctx: self.set_result_from_ctx(ctx, 'n')))
		self.run_command_and_check_result(executor, 'number 8', 8)
		self.run_command_and_check_result(executor, 'number 8.0', 8.0)
		self.run_command_and_check_result(executor, 'number -1.56e-9', -1.56e-9)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'number 48595')
		self.assertRaises(InvalidNumber, self.run_command, executor, 'number xxx')

	def test_7_text(self):
		executor = Literal('text').then(Text('t').runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text "quote"', '"quote"')
		self.assertRaises(UnknownCommand, self.run_command, executor, 'text ')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text awa awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text "try to quote"')

		executor = Literal('text').then(Text('t').in_length_range(5, 10).runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text 12345', '12345')
		self.run_command_and_check_result(executor, 'text 1234567890', '1234567890')
		self.assertRaises(TextLengthOutOfRange, self.run_command, executor, 'text 1234')
		self.assertRaises(TextLengthOutOfRange, self.run_command, executor, 'text 12345678901')

	def test_8_quote_text(self):
		executor = Literal('text').then(QuotableText('t').runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text "quote"', 'quote')
		self.run_command_and_check_result(executor, 'text "try to quote"', 'try to quote')
		self.run_command_and_check_result(executor, r'text "aa\"bb\\cc"', r'aa"bb\cc')
		self.run_command_and_check_result(executor, r'text "\\\\\"ww"', r'\\"ww')
		self.assertRaises(UnclosedQuotedString, self.run_command, executor, 'text "un quote')
		self.assertRaises(IllegalEscapesUsage, self.run_command, executor, r'text "random escaping \w"')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text awa awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text "a b c" awa')

		executor2 = Literal('text').then(QuotableText('t').allow_empty().runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.assertRaises(EmptyText, self.run_command, executor, 'text ""')
		self.run_command_and_check_result(executor2, 'text ""', '')

		executor = Literal('text').then(QuotableText('t').in_length_range(5, 10).runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text "1234567890"', '1234567890')
		self.assertRaises(TextLengthOutOfRange, self.run_command, executor, 'text 12345678901')
		self.assertRaises(TextLengthOutOfRange, self.run_command, executor, 'text "12345678901"')

	def test_9_greedy_text(self):
		executor = Literal('text').then(GreedyText('t').runs(lambda s, ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text abc de f', 'abc de f')
		self.run_command_and_check_result(executor, 'text "abc "de f', '"abc "de f')
		self.run_command_and_check_result(executor, r'text d(&sg^\bnSA', r'd(&sg^\bnSA')

	def test_10_arg_multi(self):
		executor = Literal('test').then(
			Integer('a').then(
				Float('b').in_range(10, 20).then(
					Text('t').
					runs(lambda s, ctx: self.set_result((ctx['a'], ctx['b'], ctx['t'])))
				)
			)
		).then(
			Literal('literal').then(
				Number('n').
				runs(lambda s, ctx: self.set_result_from_ctx(ctx, 'n'))
			).
			runs(self.callback_hit).
			then(Literal('dead'))
		)
		self.run_command_and_check_result(executor, 'test 9 12.3 awa', (9, 12.3, 'awa'))
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'test 9 58 awa')
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'test 81 -.01 awa')
		self.assertRaises(InvalidFloat, self.run_command, executor, 'test 81 --.01 awa')
		self.assertRaises(InvalidFloat, self.run_command, executor, 'test -5 xxx awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test -5 20 xxx yyy')
		self.assertRaises(InvalidInteger, self.run_command, executor, 'test not_literal')  # literal node all fails, try integer node

		self.run_command_and_check_hit(executor, 'test literal', True)
		self.run_command_and_check_result(executor, 'test literal 100', 100)
		self.assertRaises(InvalidNumber, self.run_command, executor, 'test literal 100x')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test literal 100 x')

		self.assertRaises(UnknownCommand, self.run_command, executor, 'test literal dead')

	def test_11_permission(self):
		def assert_requirement_not_met_message(root: Literal, command: str, message: str):
			try:
				self.run_command(root, command)
			except RequirementNotMet as e:
				self.assertEqual((message,), e.get_error_data())
			else:
				self.assertTrue(False, "RequirementNotMet doesn't raise")

		executor = Literal('permission').then(
			Literal('cannot').requires(lambda s: False).runs(self.callback_hit)
		).then(
			Literal('pass').requires(lambda s: True).runs(self.callback_hit).then(
				Literal('fail').requires(lambda s: False)
			)
		).then(
			Literal('fail').requires(lambda s: False, lambda: 'FAIL MESSAGE').runs(self.callback_hit)
		)
		self.run_command_and_check_hit(executor, 'permission pass', True)
		self.assertRaises(RequirementNotMet, self.run_command, executor, 'permission cannot')
		self.assertRaises(RequirementNotMet, self.run_command, executor, 'permission fail')
		self.assertRaises(RequirementNotMet, self.run_command, executor, 'permission pass fail')
		assert_requirement_not_met_message(executor, 'permission fail', 'FAIL MESSAGE')

		# chained requires
		executor = (
			Literal('permission').
			requires(lambda: flag_1, lambda: 'err1').
			requires(lambda: flag_2, lambda: 'err2').
			runs(self.callback_hit)
		)
		flag_1, flag_2 = True, True
		self.run_command_and_check_hit(executor, 'permission', True)
		flag_1, flag_2 = False, True
		assert_requirement_not_met_message(executor, 'permission', 'err1')
		flag_1, flag_2 = True, False
		assert_requirement_not_met_message(executor, 'permission', 'err2')
		flag_1, flag_2 = False, False
		assert_requirement_not_met_message(executor, 'permission', 'err1')

	def test_12_redirect(self):
		allow_teleport = True
		allow_tp = True

		executor1 = Literal('tp').requires(lambda s: allow_tp).then(
			Literal('here').then(
				Literal('there').runs(self.callback_hit)
			)
		)
		executor2 = Literal('teleport').requires(lambda s: allow_teleport).redirects(executor1)
		self.run_command_and_check_hit(executor1, 'tp here there', True)
		self.run_command_and_check_hit(executor2, 'teleport here there', True)
		self.assertRaises(UnknownCommand, self.run_command, executor2, 'teleport here')

		allow_tp = True
		allow_teleport = False
		self.run_command_and_check_hit(executor1, 'tp here there', True)
		self.assertRaises(RequirementNotMet, self.run_command, executor2, 'teleport here there')

		allow_tp = False
		allow_teleport = True
		self.assertRaises(RequirementNotMet, self.run_command, executor1, 'tp here there')
		self.run_command_and_check_hit(executor2, 'teleport here there', True)

		allow_tp = False
		allow_teleport = False
		self.assertRaises(RequirementNotMet, self.run_command, executor1, 'tp here there')
		self.assertRaises(RequirementNotMet, self.run_command, executor2, 'teleport here there')

	def test_13_error_listener(self):
		executor = Literal('error').then(
			Literal('ping').
			on_error(UnknownCommand, lambda s, e: self.assertIsInstance(e, UnknownCommand)).
			on_error(UnknownArgument, lambda s, e: self.assertIsInstance(e, UnknownArgument))
		).then(
			Literal('text').
			then(
				QuotableText('t').in_length_range(5, 10)
			).on_child_error(
				IllegalEscapesUsage, lambda s, e: self.callback_hit(s, {})
			)
		).then(
			Integer('w').on_error(InvalidInteger, lambda s, e: self.callback_hit(s, {}))
		).on_error(
			UnknownCommand, lambda s, e: self.callback_hit(s, {})
		).on_child_error(
			TextLengthOutOfRange, lambda s, e: self.callback_hit(s, {})
		)
		self.assertRaises(UnknownCommand, self.run_command, executor, 'error ping')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'error ping awa')
		self.assert_raises_and_check_hit(True, UnknownCommand, self.run_command, executor, 'error')
		self.assert_raises_and_check_hit(True, UnknownCommand, self.run_command, executor, 'error')
		self.assert_raises_and_check_hit(True, InvalidInteger, self.run_command, executor, 'error 10x')
		self.assert_raises_and_check_hit(True, CommandError, self.run_command, executor, 'error 10x')  # using parent error class

		self.assert_raises_and_check_hit(False, UnknownCommand, self.run_command, executor, 'error text')
		self.assert_raises_and_check_hit(True, TextLengthOutOfRange, self.run_command, executor, 'error text abc')
		self.assert_raises_and_check_hit(True, IllegalEscapesUsage, self.run_command, executor, r'error text "ab\c"')
		self.assert_raises_and_check_hit(False, UnclosedQuotedString, self.run_command, executor, 'error text "abc')

	def test_14_error_listener_only_1_catch(self):
		# https://github.com/MCDReforged/MCDReforged/issues/109
		counter = []
		executor = Literal('test'). \
			runs(lambda: None). \
			on_error(UnknownArgument, lambda: counter.append(1)). \
			on_child_error(UnknownArgument, lambda: counter.append(1))

		self.assertRaises(UnknownArgument, self.run_command, executor, 'test bang')
		self.assertEqual(1, len(counter))

		executor.then(Literal('next').runs(lambda: None))
		counter.clear()
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test bang')
		self.assertEqual(1, len(counter))

	def test_15_callback(self):
		def func1():
			self.has_hit = True

		def func2(p1):
			func1()

		def func3(p1, p2):
			func1()

		def func4(p1, p2, p3):
			func1()

		class _C:
			# noinspection PyMethodMayBeStatic
			def method(self, p1, p2):
				func1()
		self.run_command_and_check_hit(Literal('test').runs(func1), 'test', True)
		self.run_command_and_check_hit(Literal('test').runs(func2), 'test', True)
		self.run_command_and_check_hit(Literal('test').runs(func3), 'test', True)
		self.run_command_and_check_hit(Literal('test').runs(_C().method), 'test', True)
		try:
			# noinspection PyTypeChecker
			self.run_command(Literal('test').runs(func4), 'test')
		except Exception as e:
			self.assertIsInstance(e, CallbackError)
			self.assertIsInstance(e.exception, TypeError)
			self.check_hit(False)
		else:
			self.fail('Expected CallbackError but nothing raised')

	def test_16_boolean(self):
		def func(src, ctx):
			self.result = ctx['bl']
		root = Literal('test').then(Boolean('bl').runs(func))
		self.run_command_and_check_result(root, 'test true', True)
		self.run_command_and_check_result(root, 'test tRue', True)
		self.run_command_and_check_result(root, 'test FALSE', False)
		self.assertRaises(InvalidBoolean, self.run_command, root, 'test T')

	def test_17_enumeration(self):
		class MyEnum(Enum):
			a = 1
			bb = 2
			c = 'c'
			efg = ()

		def func(src, ctx):
			self.assertIsInstance(ctx['e'], MyEnum)
			self.result = ctx['e']
			self.has_hit = True

		node = Enumeration('e', MyEnum)
		root = Literal('test').then(node.runs(func))
		self.run_command_and_check_result(root, 'test a', MyEnum.a)
		self.run_command_and_check_result(root, 'test efg', MyEnum.efg)
		self.assertRaises(InvalidEnumeration, self.run_command, root, 'test nope')
		self.assertRaises(InvalidEnumeration, self.run_command, root, 'test A')

		suggestions = list(map(lambda s: s.suggest_input, root._entry_generate_suggestions(_TestCommandSource(), 'test ')))
		self.assertEqual(len(MyEnum), len(suggestions))
		for suggestion in suggestions:
			self.run_command_and_check_hit(root, 'test {}'.format(suggestion), True)

	def test_17_counting_literal(self):
		def callback(src, ctx: dict):
			self.result = (ctx.get('foo'), ctx.get('bar'))

		root = Literal('test').runs(callback)
		root.then(CountingLiteral('ping', 'foo').redirects(root))
		root.then(CountingLiteral('pong', 'bar').redirects(root))

		self.run_command_and_check_result(root, 'test', (None, None))
		self.run_command_and_check_result(root, 'test ping', (1, None))
		self.run_command_and_check_result(root, 'test ping pong ping', (2, 1))
		self.run_command_and_check_result(root, 'test pong pong pong', (None, 3))

	def test_18_precondition(self):
		whitelist: Set[str] = set()

		root = (
			Literal('a').
			precondition(lambda: 'a' in whitelist).
			then(Text('b').precondition(lambda: 'b' in whitelist).runs(self.callback_hit))
		)

		# Notes: precondition has no effect on root node for now
		self.assertRaises(UnknownCommand, self.run_command, root, 'a')
		self.assertRaises(UnknownArgument, self.run_command, root, 'a b')

		whitelist.add('b')
		self.assertRaises(UnknownCommand, self.run_command, root, 'a')
		self.run_command_and_check_hit(root, 'a b', True)


class SimpleCommandBuilderTestCase(CommandTestCase):
	def test_1_basic(self):
		builder = SimpleCommandBuilder()
		builder.command('foo bar', self.callback_hit)
		nodes = builder.build()

		self.assertEqual(1, len(nodes))
		self.assertEqual(1, len(nodes[0].get_children()))
		child = nodes[0].get_children()[0]
		self.assertIsInstance(child, Literal)
		self.assertEqual(child.literals, {'bar'})
		self.run_command_and_check_hit(self.cast(Literal, nodes[0]), 'foo bar', True)

	# noinspection PyUnresolvedReferences
	def test_2_node_order(self):
		builder = SimpleCommandBuilder()
		builder.command('a z', lambda: None)
		builder.command('b b', lambda: None)
		builder.command('c y', lambda: None)
		nodes = builder.build()

		self.assertEqual(3, len(nodes))
		self.assertTrue(all(map(lambda n: isinstance(n, Literal), nodes)))
		self.assertEqual(nodes[0].literals, {'a'})
		self.assertEqual(nodes[1].literals, {'b'})
		self.assertEqual(nodes[2].literals, {'c'})

	def test_3_node_merge(self):
		builder = SimpleCommandBuilder()
		builder.command('foo bar', lambda: None)
		builder.command('foo rab', lambda: None)
		builder.command('oof bar', lambda: None)
		builder.command('oof bar www', lambda: None)
		nodes = builder.build()

		self.assertEqual(2, len(nodes))
		self.assertEqual(1, len(nodes[1].get_children()))

	# noinspection PyUnresolvedReferences
	def test_4_defined_arg(self):
		def test_new_arg(name: str, clazz: Type[ArgumentNode]):
			def make_arg(n: str):
				self.assertEqual(name, n)
				nonlocal cnt
				cnt += 1
				return clazz(n)

			builder.arg(name, make_arg)

		cnt = 0

		builder = SimpleCommandBuilder()
		builder.command('test another <arg>', lambda: None)
		builder.command('test <word>', lambda: None)
		builder.command('test <arg>', lambda: None)
		test_new_arg('word', Text)
		test_new_arg('arg', Number)
		nodes = builder.build()

		self.assertEqual(3, cnt)  # <word>*1, <arg>*2, 1 + 2 = 3
		self.assertEqual(1, len(nodes))
		self.assertEqual(3, len(nodes[0].get_children()))
		self.assertEqual('word', nodes[0].get_children()[1].get_name())
		self.assertEqual('arg', nodes[0].get_children()[2].get_name())

	def test_5_undefined_arg(self):
		builder = SimpleCommandBuilder()
		builder.command('test <arg>', lambda: None)

		self.assertRaises(SimpleCommandBuilder.Error, builder.build)

	def test_6_defined_literal(self):
		builder = SimpleCommandBuilder()
		builder.command('test l1', lambda: None)
		builder.command('test l1 l2', lambda: None)
		builder.command('abc test', lambda: None)

		node = Literal('test')
		builder.literal('test', lambda _: node)

		nodes = builder.build()

		self.assertEqual(2, len(nodes))
		self.assertIs(node, nodes[0])
		self.assertEqual(1, len(nodes[1].get_children()))
		self.assertIs(node, nodes[1].get_children()[0])

	def test_6_undefined_literal(self):
		builder = SimpleCommandBuilder()
		builder.command('a a', lambda: None)

		nodes = builder.build()

		self.assertEqual(1, len(nodes))
		self.assertEqual(1, len(nodes[0].get_children()))
		self.assertIsNot(nodes[0], nodes[0].get_children()[0])

	def test_7_node_def_using(self):
		for i in range(2):
			builder = SimpleCommandBuilder()
			builder.command('a <b>', lambda: None)

			def_ = builder.arg('b', Integer)
			if i == 1:
				def_ = builder.literal('a')
			self.assertIsInstance(def_, NodeDefinition)
			def_.requires(lambda n: False)
			def_.on_error(RequirementNotMet, lambda src, err, ctx: self.callback_hit(src, ctx))

			nodes = builder.build()
			self.assertEqual(1, len(nodes))
			self.assertRaises(RequirementNotMet, self.run_command, nodes[0], 'a 1')
			self.check_hit(True)

	def test_8_node_def_process_amount(self):
		def post_processor(node):
			nonlocal cnt
			cnt += 1

		cnt = 0

		builder = SimpleCommandBuilder()
		builder.command('a <arg>', lambda: None)
		builder.command('b <arg>', lambda: None)
		builder.command('c <arg> <arg>', lambda: None)
		builder.arg('arg', Integer).post_process(post_processor)

		builder.build()
		self.assertEqual(4, cnt)

	def test_9_command_method_as_decorator(self):
		builder = SimpleCommandBuilder()

		@builder.command('foo a')
		def foobar_a():
			self.set_result('foobar_a')

		@builder.command('foo b')
		@builder.command('foo c <arg>')
		def foobar_bc():
			self.set_result('foobar_bc')

		builder.arg('arg', Integer)
		nodes = builder.build()
		self.assertEqual(1, len(nodes))

		node = self.cast(Literal, nodes[0])
		self.run_command_and_check_result(node, 'foo a', 'foobar_a')
		self.run_command_and_check_result(node, 'foo b', 'foobar_bc')
		self.run_command_and_check_result(node, 'foo c 123', 'foobar_bc')


class CommandToolsTestCase(CommandTestCase):
	def test_1_requirements(self):
		builder = SimpleCommandBuilder()
		builder.command('r a test', self.callback_hit)
		builder.command('r b <arg> test', self.callback_hit)
		builder.arg('arg', Integer)
		builder.literal('test').requires(Requirements.argument_exists('arg'))

		nodes = builder.build()
		self.assertEqual(1, len(nodes))
		self.assertRaises(RequirementNotMet, self.run_command, nodes[0], 'r a test')
		self.check_hit(False)
		self.run_command_and_check_hit(self.cast(Literal, nodes[0]), 'r b 123 test', True)


if __name__ == '__main__':
	unittest.main()
