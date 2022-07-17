import inspect
import threading
import unittest

from mcdreforged.api.decorator import new_thread, FunctionThread


class MyTestCase(unittest.TestCase):
	TIME_OUT = 5  # seconds

	def wait_event(self, event: threading.Event):
		ret = event.wait(timeout=self.TIME_OUT)
		self.assertTrue(ret)

	def test_1_basic(self):
		@new_thread()
		def bla1(value):
			self.assertNotEqual(threading.current_thread(), threading.main_thread())

		@new_thread
		def bla2(value):
			self.assertNotEqual(threading.current_thread(), threading.main_thread())

		@new_thread('awa')
		def bla3(value):
			self.assertNotEqual(threading.current_thread(), threading.main_thread())
			self.assertEqual(threading.current_thread().getName(), 'awa')

		threads = []
		for i, func in enumerate([bla1, bla2, bla3]):
			self.assertEqual(inspect.getfullargspec(func), inspect.getfullargspec(func.original))
			t = func(i)
			threads.append(t)

		for t in threads:
			t.join()

	def test_2_return_value(self):
		event = threading.Event()

		def func1():
			self.wait_event(event)
			return 123

		func2 = new_thread(func1)
		self.assertIs(func2.original, func1)

		t: FunctionThread = func2()
		self.assertTrue(t.is_alive())
		self.assertTrue(t.isDaemon())
		with self.assertRaises(RuntimeError):
			# the thread is still running, operation failed
			t.get_return_value()
		event.set()
		self.assertEqual(t.get_return_value(block=True, timeout=self.TIME_OUT), 123)


if __name__ == '__main__':
	unittest.main()
