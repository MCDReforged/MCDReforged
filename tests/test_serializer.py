import re
import sys
import unittest
import uuid
from enum import Enum, auto, IntFlag, IntEnum, Flag
from typing import List, Dict, Union, Optional, Any, Literal, TypeVar, Generic

from mcdreforged.api.utils import serialize, deserialize, Serializable

_py39 = sys.version_info >= (3, 9)

T = TypeVar('T')
K = TypeVar('K')
V = TypeVar('V')


class Point(Serializable):
	x: float = 1.1
	y: float = 1.2


class ConfigImpl(Serializable):
	a: int = 1
	b: str = 'b'
	c: Point = Point()
	d: List[Point] = []
	e: Dict[str, Point] = {}


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
		self.assertEqual(point, point)
		self.assertEqual(serialize(point), {'x': 0.1, 'y': 0.2})
		self.assertEqual(deserialize({'x': 0.1, 'y': 0.2}, Point), point)
		self.assertEqual(deserialize({'x': 0.1, 'y': 0.2}, Point, error_at_missing=True, error_at_redundancy=True), point)
		self.assertEqual(deserialize({}, Point), Point())
		self.assertRaises(ValueError, deserialize, {'x': 1}, Point, error_at_missing=True)
		self.assertRaises(ValueError, deserialize, {'z': 1}, Point, error_at_redundancy=True)
		self.assertRaises(TypeError, deserialize, {'x': []}, Point)
		self.assertRaises(TypeError, deserialize, {'x': set()}, Point)

	def test_2_complex_class(self):
		a1 = ConfigImpl()
		a2 = ConfigImpl()
		self.assertEqual(a1, deserialize(serialize(a1), ConfigImpl))
		self.assertEqual(a1, a2)

		data = {
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
		}
		b1 = deserialize(data, ConfigImpl)
		b2 = deserialize(data, ConfigImpl)
		b3 = deserialize(data, ConfigImpl)
		b4 = deserialize(data, ConfigImpl)
		b3.a = 22
		b4.e['park'] = Point(x=7, y=9)
		self.assertEqual(b1, deserialize(serialize(b1), ConfigImpl))
		self.assertEqual(b1, b2)
		self.assertEqual(b2, b1)
		self.assertNotEqual(b1, b3)
		self.assertNotEqual(b1, b4)

		self.assertRaises(TypeError, deserialize, {'e': object()}, ConfigImpl)

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
		self.assertFalse(Cls.deserialize({}).lst is Cls.lst)

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
		class Item:
			idx: int

		class Cls(Serializable):
			a: Union[int, str, list]
			b: Optional[float] = None
			c: Union[float, dict]
			d: Union[float, dict, Item]

		cls = Cls.deserialize({'a': 1})
		self.assertEqual(cls.a, 1)
		self.assertEqual(cls.b, None)

		cls = Cls.deserialize({'a': 'x', 'b': None})
		self.assertEqual(cls.a, 'x')
		self.assertEqual(cls.b, None)

		cls = Cls.deserialize({'a': [1], 'b': 1.2})
		self.assertEqual(cls.a, [1])
		self.assertEqual(cls.b, 1.2)

		self.assertEqual(Cls.deserialize({'c': 1.1}).c, 1.1)
		# the float converting attempt should be failed
		self.assertEqual(Cls.deserialize({'c': {'x': 'y'}}).c, {'x': 'y'})

		# dict converting tried first
		cls = Cls.deserialize({'d': {'idx': 10}})
		self.assertNotIsInstance(cls.d, Item)
		self.assertEqual(cls.d, {'idx': 10})

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
			except Exception:
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

	def test_8_subclass(self):
		class A:
			a: int = 1

		class B:
			b: str = 'bb'

		class C(A, B):
			c: bool = False

		o = C()
		o.a, o.b, o.c = 2, 'BB', True
		o2 = deserialize(serialize(o), type(o))
		self.assertEqual(o2.a, o.a)
		self.assertEqual(o2.b, o.b)
		self.assertEqual(o2.c, o.c)

	def test_9_not_friendly_constructor(self):
		class BadClass:
			value: int

			def __init__(self, value: int):  # there shouldn't be necessary parameter in the constructor
				self.value = value

		self.assertRaises(TypeError, deserialize, {'value': 1}, BadClass)

	def test_10_any(self):
		class A(Serializable):
			a: Any = 2
			b: Dict[str, Any] = {'b': True}

		a = A.get_default()
		self.assertEqual(a.a, 2)
		self.assertEqual(a.b.get('b'), True)

		a = deserialize({'a': 'x', 'b': {'key': 'value', 'something': set()}}, A)
		self.assertEqual(a.a, 'x')
		self.assertEqual(a.b.get('key'), 'value')
		self.assertIsInstance(a.b.get('something'), set)

	def test_11_py39_type_hint(self):
		# see pep-0585
		if _py39:
			# suppressing these inspections so no complain with python <3.9
			# noinspection PyTypeHints,PyUnresolvedReferences
			class A(Serializable):
				a: list[int] = [1]
				b: dict[str, bool] = {'yes': True}

			a = A.get_default()
			self.assertIsInstance(a.a, list)
			self.assertEqual(a.a, [1])
			self.assertIsInstance(a.b, dict)
			self.assertEqual(a.b.get('yes'), True)

			a = deserialize({'a': [3, 4], 'b': {'no': False}}, A)
			self.assertEqual(a.a, [3, 4])
			self.assertEqual(a.b.get('no'), False)
		else:
			print('Ignored type hint test which uses python 3.9 feature')

	def test_12_literal(self):
		class A(Serializable):
			a: Literal[1, 2, '3'] = 2
			b: Dict[str, Literal['x', 'y', 'z']]

		a = A.get_default()
		self.assertEqual(a.a, 2)

		a = deserialize({'a': '3', 'b': {'k': 'x'}}, A)
		self.assertEqual(a.a, '3')
		self.assertEqual(a.b, {'k': 'x'})

		a = deserialize({'b': {}}, A)
		self.assertEqual(a.a, 2)
		self.assertEqual(a.b, {})

		with self.assertRaises(ValueError):
			deserialize({'a': 4}, A)
		with self.assertRaises(ValueError):
			deserialize({'b': {'k': 'u'}}, A)

	def test_13_serialize_order(self):
		class Data(Serializable):
			a: int
			b: Dict[str, str] = {'b': True}

		x = Data()
		self.assertEqual(['b'], list(filter(lambda k: not k.startswith('_'), vars(x).keys())))
		self.assertEqual(['b'], list(x.serialize().keys()))

		# order of known fields are preserved
		y = Data()
		y.a = 2
		self.assertEqual(['b', 'a'], list(filter(lambda k: not k.startswith('_'), vars(y).keys())))
		self.assertEqual(['a', 'b'], list(y.serialize().keys()))

		# unknown fields are thrown to the end
		z = Data()
		z.c = 'foobar'
		z.a = 2
		self.assertEqual(['b', 'c', 'a'], list(filter(lambda k: not k.startswith('_'), vars(z).keys())))
		self.assertEqual(['a', 'b', 'c'], list(z.serialize().keys()))

	def test_14_deepcopy(self):
		class Item(Serializable):
			a: str
			b: float

		class Data(Serializable):
			a: int = 543
			b: Dict[str, str] = {'b': 'B'}
			c: List[Dict[int, int]] = [{1: 11}, {2: -2, 3: -3}]
			d: Item

		x = Data(a=308, b={}, c=[{3: 9}, {6: 36}], d=Item(a='x', b=3.4))
		y = x.copy()
		self.assertEqual(x, y)
		self.assertIsNot(x.b, y.b)
		self.assertIsNot(x.c, y.c)
		for i in range(len(x.c)):
			self.assertIsNot(x.c[i], y.c[i])

		z = y.copy()
		z.b['X'] = 'x'
		self.assertNotEqual(x, z)

	def test_15_deserialize_validation_callback(self):
		this = self
		counter = 0

		class Data(Serializable):
			attr: List[int] = [3]

			def validate_attribute(self, attr_name: str, attr_value: Any, **kwargs):
				this.assertEqual(attr_name, 'attr')
				this.assertEqual(value_1, attr_value)
				nonlocal counter
				counter += 1
				raise ValueError('foobar')

		value_1 = [1, 2, 4, 3]

		# nothing happens in non-deserialization operations
		a = Data(attr=value_1)
		a.copy()
		a.get_default()
		self.assertEqual(0, counter)

		# callback gets invoked once
		self.assertRaisesRegex(ValueError, 'foobar', lambda: Data.deserialize({'attr': value_1}))
		self.assertEqual(1, counter)

	def test_16_deserialize_finish_callback(self):
		counter = 0

		class Data(Serializable):
			def on_deserialization(self, **kwargs):
				nonlocal counter
				counter += 1

		# nothing happens in non-deserialization operations
		a = Data()
		a.copy()
		a.get_default()
		self.assertEqual(0, counter)

		# callback gets invoked once
		Data.deserialize({})
		self.assertEqual(1, counter)

	def test_17_get_field_annotations(self):
		class Data(Serializable):
			a: int
			b: Optional[float]
			c: Dict[str, Union[str, int]]
			d: List[Any]

		x = Data.get_field_annotations()
		self.assertIsInstance(x, dict)
		self.assertEqual(x.get('a'), int)
		self.assertEqual(x.get('b'), Optional[float])
		self.assertEqual(x.get('c'), Dict[str, Union[str, int]])
		self.assertEqual(x.get('d'), List[Any])

		y = Data.get_field_annotations()
		self.assertIs(x, y)  # test cache

	def test_18_inherit_base_class(self):
		class MyInt(int):
			pass

		class MyStr(str):
			def __init__(self, s: str):
				if not isinstance(s, str):
					raise TypeError(type(s))
				self.num = int(s[:-1])
				self.unit = s[-1]

		class MyList(List[int]):
			pass

		class MyDict(dict):
			pass

		class MyDictG(Generic[K, V], dict):
			pass

		class Data(Serializable):
			a: MyInt = MyInt(123)
			b: MyStr = MyStr('1m')
			c: MyList = MyList([1, 2, 3])
			d: MyDict = MyDict({'a': 0.4})
			e: MyDictG[MyStr, MyInt] = MyDict({'1b': 7})

		x = Data.get_default().serialize()
		self.assertEqual(type(x['a']), int)
		self.assertEqual(type(x['b']), str)
		self.assertEqual(type(x['c']), list)
		self.assertEqual(type(x['d']), dict)
		self.assertEqual(type(x['e']), dict)
		self.assertEqual(x['a'], 123)
		self.assertEqual(x['b'], '1m')
		self.assertEqual(x['c'], [1, 2, 3])
		self.assertEqual(x['d'], {'a': 0.4})
		self.assertEqual(x['e'], {'1b': 7})

		y = Data.deserialize({
			'a': 789,
			'b': '30s',
			'c': [-4],
			'e': {'3x': 0},
		})
		self.assertEqual(type(y.a), MyInt)
		self.assertEqual(type(y.b), MyStr)
		self.assertEqual(type(y.c), MyList)
		self.assertEqual(type(y.d), MyDict)
		self.assertEqual(type(y.e), MyDictG)
		self.assertEqual(type(y.e), MyDictG)
		self.assertEqual(y.a, 789)
		self.assertEqual(y.b, '30s')
		self.assertEqual(y.b.num, 30)
		self.assertEqual(y.b.unit, 's')
		self.assertEqual(y.c, [-4])
		self.assertEqual(y.d, {'a': 0.4})
		self.assertEqual(y.d['a'], 0.4)
		self.assertEqual(y.e, {'3x': 0})
		self.assertEqual(y.e['3x'], 0)

		k, v = next(iter(y.e.items()))
		self.assertEqual(type(k), MyStr)
		self.assertEqual(k, MyStr('3x'))
		self.assertEqual(k, '3x')
		self.assertEqual(type(v), MyInt)
		self.assertEqual(v, MyInt(0))
		self.assertEqual(v, 0)

	def test_19_re_pattern(self):
		for regex_val in [r'^[a-zA-Z]{3}\d$', rb'^[a-zA-Z]{3}\d$']:
			class Data(Serializable):
				regex: re.Pattern = re.compile(regex_val)

			regex_str = regex_val
			if isinstance(regex_str, bytes):
				regex_str = regex_str.decode('utf8')

			x = Data.get_default()
			self.assertEqual(type(x.regex), re.Pattern)
			self.assertEqual(x.regex.pattern, regex_val)

			y = x.serialize()
			self.assertIsInstance(y['regex'], str)
			self.assertEqual({'regex': regex_str}, y)

			z = Data.deserialize(y)
			self.assertEqual(type(z.regex), re.Pattern)
			self.assertEqual(z.regex.pattern, regex_str)

		with self.assertRaises(ValueError) as cm:
			Data.deserialize({'regex': r'[a-z'})
		self.assertIsInstance(cm.exception, ValueError)
		self.assertIn('Invalid regular expression'.lower(), str(cm.exception).lower())

	def test_20_uuid(self):
		for uuid_str in [
			'f4a23ecc-3994-4409-affe-e2dc33cbfec2',
			'74272dbd-658e-453c-bcdc-7270b5e08442'.replace('-', ''),
		]:
			class Data(Serializable):
				u: uuid.UUID = uuid.UUID(hex=uuid_str)

			uuid_str_std = str(uuid.UUID(uuid_str))
			x = Data.get_default()
			self.assertEqual(type(x.u), uuid.UUID)
			self.assertEqual(str(x.u), uuid_str_std)

			y = x.serialize()
			self.assertIsInstance(y['u'], str)
			self.assertEqual({'u': uuid_str_std}, y)

			z = Data.deserialize(y)
			self.assertEqual(type(z.u), uuid.UUID)
			self.assertEqual(z.u, x.u)

		with self.assertRaises(ValueError) as cm:
			Data.deserialize({'u': '244b28ca-899b-4d'})
		self.assertIsInstance(cm.exception, ValueError)
		self.assertIn('Invalid uuid'.lower(), str(cm.exception).lower())


if __name__ == '__main__':
	unittest.main()
