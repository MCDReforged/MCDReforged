import unittest
from typing import List, Dict

from mcdreforged.api.utils import serialize, deserialize, Serializable


class Point:
	x: float = 1.1
	y: float = 1.2

	def __str__(self):
		return '({}, {})'.format(self.x, self.y)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return isinstance(other, type(self)) and other.x == self.x and other.y == self.y


class ConfigImpl:
	a: int = 1
	b: str = 'b'
	c: Point = Point()
	d: List[Point] = []
	e: Dict[str, Point] = {}

	def __str__(self):
		return 'a={}, b={}, c={}, d={}, e={}'.format(self.a, self.b, self.c, self.d, self.e)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return isinstance(other, type(self)) and \
			other.a == self.a and other.b == self.b and \
			other.c == self.c and other.d == self.d and \
			other.e == self.e


class MyTestCase(unittest.TestCase):
	def test_0_simple(self):
		point = Point()
		point.x = 0.1
		point.y = 0.2
		self.assertEqual(serialize(point), {'x': 0.1, 'y': 0.2})
		self.assertEqual(deserialize({'x': 0.1, 'y': 0.2}, Point), point)
		self.assertEqual(deserialize({'x': 0.1, 'y': 0.2}, Point, error_at_missing=True, error_at_redundancy=True), point)
		self.assertEqual(deserialize({}, Point), Point())
		self.assertRaises(ValueError, deserialize, {'x': 1}, Point, error_at_missing=True)
		self.assertRaises(ValueError, deserialize, {'z': 1}, Point, error_at_redundancy=True)
		self.assertRaises(TypeError, deserialize, {'x': []}, Point)

	def test_1_dict(self):
		data = {'a': 1, 'b': 'xx', 'c': [1, 2, 3], 'd': {'w': 'ww'}}
		self.assertEqual(data, serialize(data))
		self.assertEqual(data, deserialize(data, dict))

	def test_2_complex(self):
		a = ConfigImpl()
		self.assertEqual(a, deserialize(serialize(a), ConfigImpl))
		b = deserialize({
			'a': 11,
			'b': 'bb',
			'c': {'x': 3, 'y': 4},
			'd': [
				{'x': 10, 'y': 23},
				{'x': 11, 'y': 24}
			],
			'e': {
				'home': {'x': 33, 'y': 24},
				'park': {'x': -3, 'y': 2.4}
			}
		}, ConfigImpl)
		self.assertEqual(b, deserialize(serialize(b), ConfigImpl))

	def test_3_copy(self):
		class Cls(Serializable):
			lst: List[int] = []

		self.assertEqual(0, len(Cls.lst))
		self.assertEqual(0, len(Cls.deserialize({}).lst))
		obj = Cls.deserialize({})
		for i in range(10):
			obj.lst.append(i)
		self.assertEqual(10, len(obj.lst))
		self.assertEqual(0, len(Cls.deserialize({}).lst))
		self.assertEqual(0, len(Cls().lst))


if __name__ == '__main__':
	unittest.main()
