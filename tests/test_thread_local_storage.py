import asyncio
import threading
import unittest
from typing import Union

from typing_extensions import Self

from mcdreforged.utils.thread_local_storage import ThreadLocalStorage


class Value:
	def __init__(self, v: int):
		self.v = v

	def __eq__(self, other: Union[Self, int]):
		if isinstance(other, int):
			other = Value(other)
		return self.v == other.v


class MyTestCase(unittest.TestCase):
	def test_threading(self):
		tls = ThreadLocalStorage()
		tls.put(1)

		def another():
			tls.put(2)
			self.assertEqual(2, tls.get(default=None))

		thread = threading.Thread(target=another, args=())
		thread.start()
		thread.join()
		self.assertEqual(1, tls.get(default=None))
		self.assertEqual(2, tls.get_by_thread(thread, default=None))

	def test_async(self):
		tls: ThreadLocalStorage[Value] = ThreadLocalStorage()
		tls.put(Value(1))
		print('main', id(tls.get(default=None)))

		async def async_test():
			print('main co 1', id(tls.get(default=None)))
			self.assertEqual(1, tls.get(default=None))
			tls.put(Value(2))
			self.assertEqual(2, tls.get(default=None))
			print('main co 2', id(tls.get(default=None)))

			async def child_assert(exp: int):
				self.assertEqual(exp, tls.get(default=None))

			async def child(new_value: int):
				print('child co 1', new_value, id(tls.get(default=None)))
				self.assertEqual(2, tls.get(default=None))

				tls.put(Value(new_value))
				print('child co 2', new_value, id(tls.get(default=None)))

				self.assertEqual(new_value, tls.get(default=None))
				await asyncio.sleep(0)
				self.assertEqual(new_value, tls.get(default=None))

				await child_assert(new_value)
				print('child co 3', new_value, id(tls.get(default=None)))

			for task in [
				asyncio.create_task(child(i))
				for i in range(10, 20)
			]:
				await task
			self.assertEqual(2, tls.get(default=None))

		asyncio.run(async_test())


if __name__ == '__main__':
	unittest.main()
