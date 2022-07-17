import inspect
import threading
import unittest

from mcdreforged.api.decorator import new_thread


class MyTestCase(unittest.TestCase):
	def test(self):
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


if __name__ == '__main__':
	unittest.main()
