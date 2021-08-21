import unittest
from enum import Enum, auto, IntFlag, IntEnum, Flag
from typing import List, Dict, Union, Optional

from mcdreforged.api.utils import serialize, deserialize, Serializable


class Point(Serializable):
	x: float = 1.1
	y: float = 1.2

	def __str__(self):
		return '({}, {})'.format(self.x, self.y)

	def __repr__(self):
		return self.__str__()

	def __eq__(self, other):
		return isinstance(other, type(self)) and other.x == self.x and other.y == self.y


class ConfigImpl(Serializable):
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
		for obj in (
			False, True, 0, 1, -1, 1.2, 1E9 + 7, '', 'test', None,
			[1, None, 'a'], {'x': 2, 1.3: None},
			{'a': 1, 'b': 'xx', 'c': [1, 2, 3], 'd': {'w': 'ww'}}
		):
			self.assertEqual(obj, serialize(obj))
			self.assertEqual(obj, deserialize(obj, type(obj)))

		# special case for int value converting to float
		self.assertEqual(1.0, deserialize(1, float))

		# tuple deserialized into list
		self.assertEqual([], serialize(()))
		self.assertEqual([1, 2, [3]], serialize((1, 2, (3, ))))

		# not supported types
		self.assertRaises(TypeError, serialize, {1, 2})
		self.assertRaises(TypeError, serialize, int)

		# list & dict
		# no inner element recursively deserializing due to no type hint
		for obj in (
			[lambda: 'rua', iter([1, 2])],
			{1: set({}), 'a': range(10)}
		):
			self.assertEqual(obj, deserialize(obj, type(obj)))

	def test_1_simple_class(self):
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

	def test_2_complex_class(self):
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

	def test_3_copy_default_value(self):
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

	def test_4_protected_fields(self):
		class Cls(Serializable):
			data: int = 1
			__secret: str

			def __init__(self, **kwargs):
				super().__init__(**kwargs)
				self.__secret = 'a'
				self.__secret2 = 'x'

			def get_secret(self):
				return self.__secret

			def get_secret2(self):
				return self.__secret2

		c = Cls(data=2)
		self.assertEqual('a', c.get_secret())
		self.assertEqual('x', c.get_secret2())
		self.assertEqual({'data': 2}, c.serialize())
		self.assertEqual('a', Cls.deserialize({'__secret': 'b'}).get_secret())
		self.assertEqual('x', Cls.deserialize({'__secret2': 'y'}).get_secret2())

	def test_5_union(self):
		class Cls(Serializable):
			a: Union[int, str, list]
			b: Optional[float] = None

		c = Cls.deserialize({'a': 1})
		self.assertEqual(c.a, 1)
		self.assertEqual(c.b, None)

		c = Cls.deserialize({'a': 'x', 'b': None})
		self.assertEqual(c.a, 'x')
		self.assertEqual(c.b, None)

		c = Cls.deserialize({'a': [1], 'b': 1.2})
		self.assertEqual(c.a, [1])
		self.assertEqual(c.b, 1.2)

		self.assertRaises(TypeError, Cls.deserialize, {'a': {}, 'b': 1.2})
		self.assertRaises(TypeError, Cls.deserialize, {'a': None, 'b': 1.2})
		self.assertRaises(TypeError, Cls.deserialize, {'a': 1, 'b': 'y'})

	def test_6_construct(self):
		class Points(Serializable):
			main: Point = None
			any: Optional[Serializable] = None
			collection: List[Point] = []

		p = Point(x=2, y=3)
		self.assertEqual(Point.deserialize({'x': 2, 'y': 3}), p)
		self.assertIs(Points(main=p).main, p)
		self.assertIs(Points(any=p).any, p)
		self.assertRaises(KeyError, Points, ping='pong')

	def test_7_enum(self):
		class Gender(Enum):
			male = 'man'
			female = 'woman'

		class MyData(Serializable):
			name: str = 'zhang_san'
			gender: Gender = Gender.male

		data = MyData.get_default()
		self.assertEqual({'name': 'zhang_san', 'gender': 'male'}, data.serialize())
		data.gender = Gender.female
		self.assertEqual({'name': 'zhang_san', 'gender': 'female'}, data.serialize())
		self.assertEqual(Gender.female, MyData.deserialize({'name': 'li_si', 'gender': 'female'}).gender)
		self.assertRaises(KeyError, MyData.deserialize, {'gender': 'none'})

		# auto()
		for base_class in (Enum, IntEnum, Flag, IntFlag):
			class TestEnum(base_class):
				RED = auto()
				BLUE = auto()
				GREEN = auto()

			class TestData(Serializable):
				data: TestEnum

			try:
				# noinspection PyTypeChecker
				for my_enum in TestEnum:
					serialized = TestData(data=my_enum).serialize()
					# self.assertEqual(my_enum.value, serialized['data'], msg='w')
					self.assertEqual(my_enum, TestData.deserialize(serialized).data)
			except:
				print('Error when testing with base class {}'.format(base_class))
				raise

		# special enum value
		class TestEnum(Enum):
			A = auto()
			SET = set()
			RANGE = range(5)

		for enum in TestEnum:
			self.assertIsInstance(serialize(enum), str)
			self.assertEqual(enum, deserialize(serialize(enum), TestEnum))


if __name__ == '__main__':
	unittest.main()
