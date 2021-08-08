import unittest

from mcdreforged.command.builder.command_node import *


class MyTestCase(unittest.TestCase):
	# -------------
	#   callbacks
	# -------------

	def callback_hit(self, source, ctx):
		self.has_hit = True

	def callback_dummy(self, source, ctx):
		pass

	def set_result_from_ctx(self, ctx, key):
		self.result = ctx[key]

	def set_result(self, result):
		self.result = result

	# ---------
	#   utils
	# ---------

	def run_command(self, executor: EntryNode, command):
		self.has_hit = False
		self.result = None
		# noinspection PyTypeChecker
		executor.execute(None, command)

	def check_hit(self, value: bool):
		self.assertEqual(self.has_hit, value)

	def check_result(self, result):
		self.assertEqual(type(self.result), type(result))
		self.assertEqual(self.result, result)

	def run_command_and_check_result(self, executor, command, result):
		self.run_command(executor, command)
		self.check_result(result)

	def run_command_and_check_hit(self, executor, command, value: bool):
		self.run_command(executor, command)
		self.check_hit(value)

	def assert_raises_and_check_hit(self, value: bool, error, func, *args, **kwargs):
		self.assertRaises(error, func, *args, **kwargs)
		self.check_hit(value)

	# ---------
	#   Tests
	# ---------

	def test_1_root_node(self):
		pass
		# self.assertRaises(RuntimeError, self.run_command, Number('num').run(self.callback_hit), '123')
		# self.assertRaises(RuntimeError, self.run_command, Text('t').run(self.callback_hit), 'awa')

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
		try:
			self.run_command(executor, 'permission fail')
		except RequirementNotMet as e:
			self.assertEqual(('FAIL MESSAGE',), e.get_error_data())

	def test_12_redirect(self):
		executor1 = Literal('tp').then(
			Literal('here').then(
				Literal('there').runs(self.callback_hit)
			)
		)
		let_it_pass = True
		executor2 = Literal('teleport').requires(lambda s: let_it_pass).redirects(executor1)
		self.run_command_and_check_hit(executor1, 'tp here there', True)
		self.run_command_and_check_hit(executor2, 'teleport here there', True)
		self.assertRaises(UnknownCommand, self.run_command, executor2, 'teleport here')
		let_it_pass = False
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
		# https://github.com/Fallen-Breath/MCDReforged/issues/109
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
		self.assert_raises_and_check_hit(False, TypeError, self.run_command, Literal('test').runs(func4), 'test')


if __name__ == '__main__':
	unittest.main()
