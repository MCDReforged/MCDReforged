import threading
import unittest
from typing import Iterable

from mcdreforged.api.decorator import spam_proof, new_thread, FunctionThread


class MyTestCase(unittest.TestCase):
	TIME_OUT = 5  # seconds

	def wait_event(self, event: threading.Event):
		ret = event.wait(timeout=self.TIME_OUT)
		self.assertTrue(ret)

	def join_threads(self, threads: Iterable[threading.Thread]):
		for t in threads:
			t.join(timeout=self.TIME_OUT)
			self.assertFalse(t.is_alive())

	def test_1_basic(self):
		event = threading.Event()
		expected_arg: int

		@spam_proof
		def work(arg: int):
			self.wait_event(event)
			self.assertEqual(arg, expected_arg)

		def do_work(arg: int, expected_ret: bool):
			def testing_stuffs():
				ret = work(arg)
				self.assertEqual(ret, expected_ret)

			t = threading.Thread(target=testing_stuffs)
			t.start()
			return t

		threads = [
			do_work(1, True),
			do_work(2, False),
			do_work(3, False),
		]

		expected_arg = 1
		event.set()
		self.join_threads(threads)
		threads.clear()

		event.clear()
		t = do_work(4, True)
		expected_arg = 4
		event.set()
		self.join_threads([t])

	def test_2_arg(self):
		@spam_proof
		def func1(arg: int):
			pass

		@spam_proof()
		def func2(arg: int):
			pass

		@spam_proof(lock_class=threading.Lock)
		def func3(arg: int):
			pass

		def func4(arg: int):
			pass

		self.assertIsInstance(func1.lock, type(threading.RLock()))
		self.assertIsInstance(func2.lock, type(threading.RLock()))
		self.assertIsInstance(func3.lock, type(threading.Lock()))
		func5 = spam_proof(func4)
		self.assertIs(func5.original, func4)

	def test_3_multi_decorator(self):
		event = threading.Event()
		expected_arg: int

		@new_thread
		@spam_proof
		def work(arg: int):
			self.wait_event(event)
			self.assertEqual(arg, expected_arg)

		t1: FunctionThread = work(1)  # passed
		t2: FunctionThread = work(2)  # skipped
		t3: FunctionThread = work(3)  # skipped

		self.join_threads([t2, t3])
		self.assertFalse(t2.get_return_value())
		self.assertFalse(t3.get_return_value())

		expected_arg = 1
		event.set()
		self.join_threads([t1])
		self.assertTrue(t1.get_return_value())


if __name__ == '__main__':
	unittest.main()
