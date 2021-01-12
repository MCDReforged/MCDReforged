import collections
from typing import Optional, Dict, List


class PermissionLevelItem:
	def __init__(self, name: str, level: int):
		self.name = name
		self.level = level

	def __str__(self):
		return '{} ({})'.format(self.level, self.name)

	def __repr__(self):
		return 'Permission[name={},level={}]'.format(self.name, self.level)

	def __lt__(self, other):
		if not isinstance(other, type(self)):
			return False
		return self.level < other.level


class _PermissionLevelStorage:
	STORAGE = []  # type: List[PermissionLevelItem]

	@classmethod
	def register(cls, item: PermissionLevelItem):
		cls.STORAGE.append(item)
		cls.STORAGE.sort()
		return item.level

	@classmethod
	def get_value_dict(cls):
		return collections.OrderedDict([(item.name, item.level) for item in cls.STORAGE])


class PermissionLevel:
	GUEST	= _PermissionLevelStorage.register(PermissionLevelItem('guest', 0))
	USER	= _PermissionLevelStorage.register(PermissionLevelItem('user', 1))
	HELPER	= _PermissionLevelStorage.register(PermissionLevelItem('helper', 2))
	ADMIN	= _PermissionLevelStorage.register(PermissionLevelItem('admin', 3))
	OWNER	= _PermissionLevelStorage.register(PermissionLevelItem('owner', 4))
	__NAME_DICT = collections.OrderedDict([(item.name, item) for item in _PermissionLevelStorage.STORAGE])  # type: Dict[str, PermissionLevelItem]
	__LEVEL_DICT = collections.OrderedDict([(item.level, item) for item in _PermissionLevelStorage.STORAGE])  # type: Dict[int, PermissionLevelItem]
	LEVELS = [item.level for item in _PermissionLevelStorage.STORAGE]  # type: List[int]
	NAMES = [item.name for item in _PermissionLevelStorage.STORAGE]  # type: List[str]
	INSTANCES = _PermissionLevelStorage.STORAGE.copy()  # type: List[PermissionLevelItem]

	MAXIMUM_LEVEL = LEVELS[-1]
	MINIMUM_LEVEL = LEVELS[0]
	MCDR_CONTROL_LEVEL = ADMIN
	PHYSICAL_SERVER_CONTROL_LEVEL = OWNER
	CONSOLE_LEVEL = MAXIMUM_LEVEL

	@classmethod
	def __check_range(cls, level: int):
		if cls.MINIMUM_LEVEL <= level <= cls.MAXIMUM_LEVEL:
			pass
		else:
			raise ValueError('Value {} out of range [{}, {}]'.format(level, cls.MINIMUM_LEVEL, cls.MAXIMUM_LEVEL))

	@classmethod
	def from_value(cls, value):
		"""
		Convert any type of permission level into int value. Examples:
			'guest'	-> 0
			'admin'	-> 3
			'1'		-> 1
			2		-> 2
		If the argument is invalid return None

		:param value: a permission related object
		:type value: str or int
		:rtype: PermissionLevelItem
		"""
		level = None
		if isinstance(value, str):
			if value.isdigit():
				value = int(value)
			elif value in cls.NAMES:
				level = cls.__NAME_DICT[value]
		if isinstance(value, int):
			cls.__check_range(value)
			level = cls.__LEVEL_DICT[value]
		if level is None:
			raise TypeError('Unsupported value for {}: {}'.format(cls.__name__, value))
		return level

	@classmethod
	def get_level(cls, value) -> Optional[PermissionLevelItem]:
		"""
		Fail-proof version of from_value
		"""
		try:
			return cls.from_value(value)
		except (TypeError, ValueError):
			return None
