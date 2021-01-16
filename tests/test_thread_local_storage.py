import threading
import unittest

from mcdreforged.utils.thread_local_storage import ThreadLocalStorage


class MyTestCase(unittest.TestCase):
	def test_something(self):
		tls = ThreadLocalStorage()
		tls.put('a', 1)

		def another():
			tls.put('a', 2)
			self.assertEqual(2, tls.get('a'))

		thread = threading.Thread(target=another, args=())
		thread.start()
		thread.join()
		self.assertEqual(1, tls.get('a'))
		self.assertEqual(2, tls.get('a', thread=thread))


if __name__ == '__main__':
	unittest.main()
