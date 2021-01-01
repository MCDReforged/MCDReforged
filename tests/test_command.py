import unittest

from command_builder import *


class MyTestCase(unittest.TestCase):
	# -------------
	#   callbacks
	# -------------

	def hit(self, ctx):
		self.has_hit = True

	def dummy(self, ctx):
		pass

	def set_result_from_ctx(self, ctx, key):
		self.result = ctx[key]

	def set_result(self, result):
		self.result = result

	# ---------
	#   utils
	# ---------

	def run_command(self, executor, command):
		self.has_hit = False
		self.result = None
		executor.execute(command)

	def check_hit(self, value):
		self.assertEqual(self.has_hit, value)

	def check_result(self, result):
		self.assertEqual(type(result), type(result))
		self.assertEqual(self.result, result)

	def run_command_and_check_result(self, executor, command, result):
		self.run_command(executor, command)
		self.check_result(result)

	def run_command_and_check_hit(self, executor, command, value):
		self.run_command(executor, command)
		self.check_hit(value)

	# ---------
	#   Tests
	# ---------

	def test_1_root_node(self):
		self.assertRaises(RuntimeError, self.run_command, Number('num').run(self.hit), '123')
		self.assertRaises(RuntimeError, self.run_command, Text('t').run(self.hit), 'awa')

	def test_2_literal(self):
		executor = Literal('test').run(self.hit)
		self.assertRaises(UnknownArgument, self.run_command, executor, 'awa')
		self.check_hit(False)
		self.run_command_and_check_hit(executor, 'test', True)
		self.assertRaises(UnknownArgument, self.run_command, executor, 'another')

		executor = Literal('test').then(Literal('ping').run(self.dummy)).then(Literal('pong').run(self.hit))
		self.run_command_and_check_hit(executor, 'test ping', False)
		self.run_command_and_check_hit(executor, 'test pong', True)
		self.run_command_and_check_hit(executor, 'test    pong', True)

		self.assertRaises(UnknownCommand, self.run_command, executor, 'test')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test pingpong')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test ping extra')

		self.assertRaises(TypeError, Literal, 'ab cd')

	def test_3_int(self):
		executor = Literal('int').then(Integer('i').run(lambda ctx: self.set_result_from_ctx(ctx, 'i')))
		self.run_command_and_check_result(executor, 'int 10', 10)
		self.run_command_and_check_result(executor, 'int -121', -121)
		self.assertRaises(IllegalArgument, self.run_command, executor, 'int 1.0')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'int xxx')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'int 123abc')

	def test_4_int_range(self):
		executor = Literal('int2').then(Integer('i').in_range(10, 20).run(lambda ctx: self.set_result_from_ctx(ctx, 'i')))
		self.run_command_and_check_result(executor, 'int2 10', 10)
		self.run_command_and_check_result(executor, 'int2 20', 20)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'int2 9')
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'int2 21')

	def test_5_float(self):
		executor = Literal('float').then(Float('f').in_range(-10, 20).run(lambda ctx: self.set_result_from_ctx(ctx, 'f')))
		self.run_command_and_check_result(executor, 'float 12.34', 12.34)
		self.run_command_and_check_result(executor, 'float -10.0', -10.0)
		self.run_command_and_check_result(executor, 'float 1e1', 1e1)
		self.run_command_and_check_result(executor, 'float -1.56e-9', -1.56e-9)
		self.run_command_and_check_result(executor, 'float .8', .8)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'float 1.2e9')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'float 1.2.3')

	def test_6_number(self):
		executor = Literal('number').then(Number('n').in_range(-10, 20).run(lambda ctx: self.set_result_from_ctx(ctx, 'n')))
		self.run_command_and_check_result(executor, 'number 8', 8)
		self.run_command_and_check_result(executor, 'number 8.0', 8.0)
		self.run_command_and_check_result(executor, 'number -1.56e-9', -1.56e-9)
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'number 48595')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'number xxx')

	def test_7_text(self):
		executor = Literal('text').then(Text('t').run(lambda ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text "quote"', '"quote"')
		self.assertRaises(UnknownCommand, self.run_command, executor, 'text ')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text awa awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text "try to quote"')

	def test_8_quote_text(self):
		executor = Literal('text').then(QuotableText('t').run(lambda ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text "quote"', 'quote')
		self.run_command_and_check_result(executor, 'text "try to quote"', 'try to quote')
		self.run_command_and_check_result(executor, r'text "aa\"bb\\cc"', r'aa"bb\cc')
		self.run_command_and_check_result(executor, r'text "\\\\\"ww"', r'\\"ww')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'text "un quote')
		self.assertRaises(IllegalArgument, self.run_command, executor, r'text "random escaping \w"')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text awa awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'text "a b c" awa')

		executor2 = Literal('text').then(QuotableText('t').allow_empty().run(lambda ctx: self.set_result_from_ctx(ctx, 't')))
		self.assertRaises(EmptyText, self.run_command, executor, 'text ""')
		self.run_command_and_check_result(executor2, 'text ""', '')

	def test_9_greedy_text(self):
		executor = Literal('text').then(GreedyText('t').run(lambda ctx: self.set_result_from_ctx(ctx, 't')))
		self.run_command_and_check_result(executor, 'text awa', 'awa')
		self.run_command_and_check_result(executor, 'text 123123', '123123')
		self.run_command_and_check_result(executor, 'text abc de f', 'abc de f')
		self.run_command_and_check_result(executor, 'text "abc "de f', '"abc "de f')
		self.run_command_and_check_result(executor, r'text d(&sg^\bnSA', r'd(&sg^\bnSA')

	def test_10_arg_multi(self):
		executor = Literal('test'). \
			then(Integer('a').
				then(Float('b').in_range(10, 20).
					then(Text('t').
						run(lambda ctx: self.set_result((ctx['a'], ctx['b'], ctx['t'])))
					)
				)
			). \
			then(Literal('literal').
				then(Number('n').
					run(lambda ctx: self.set_result_from_ctx(ctx, 'n'))
				).
				run(self.hit).
				then(Literal('dead'))
			)
		self.run_command_and_check_result(executor, 'test 9 12.3 awa', (9, 12.3, 'awa'))
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'test 9 58 awa')
		self.assertRaises(NumberOutOfRange, self.run_command, executor, 'test 81 -.01 awa')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'test 81 --.01 awa')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'test -5 xxx awa')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test -5 20 xxx yyy')
		self.assertRaises(IllegalArgument, self.run_command, executor, 'test not_literal')

		self.run_command_and_check_hit(executor, 'test literal', True)
		self.run_command_and_check_result(executor, 'test literal 100', 100)
		self.assertRaises(IllegalArgument, self.run_command, executor, 'test literal 100x')
		self.assertRaises(UnknownArgument, self.run_command, executor, 'test literal 100 x')

		self.assertRaises(UnknownCommand, self.run_command, executor, 'test literal dead')


if __name__ == '__main__':
	unittest.main()
