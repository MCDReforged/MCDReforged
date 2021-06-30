import json
from typing import List, Dict

from mcdreforged.utils.config import serializer


class Point:
	x: float = 1.1
	y: float = 1.2

	def __str__(self):
		return '({}, {})'.format(self.x, self.y)

	def __repr__(self):
		return self.__str__()


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


print(serializer.deserialize({'x': 10, 'y': 23}, Point))
print(serializer.deserialize({'x': 10}, Point))
a = ConfigImpl()
b = serializer.serialize(a)
print(json.dumps(b, indent=4, ensure_ascii=False))
print(serializer.deserialize(b, ConfigImpl))
print(serializer.deserialize({
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
}, ConfigImpl))
