import collections
from enum import Enum
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


class PermissionLevel:
	class __Storage(Enum):
		GUEST_	= PermissionLevelItem('guest', 0)
		USER_	= PermissionLevelItem('user', 1)
		HELPER_	= PermissionLevelItem('helper', 2)
		ADMIN_	= PermissionLevelItem('admin', 3)
		OWNER_	= PermissionLevelItem('owner', 4)

	GUEST = __Storage.GUEST_.value.level
	USER = __Storage.USER_.value.level
	HELPER = __Storage.HELPER_.value.level
	ADMIN = __Storage.ADMIN_.value.level
	OWNER = __Storage.OWNER_.value.level

	INSTANCES = [item.value for item in __Storage]  # type: List[PermissionLevelItem]
	LEVELS = [inst.level for inst in INSTANCES]  # type: List[int]
	NAMES = [inst.name for inst in INSTANCES]  # type: List[str]
	__NAME_DICT = collections.OrderedDict(zip(NAMES, INSTANCES))  # type: Dict[str, PermissionLevelItem]
	__LEVEL_DICT = collections.OrderedDict(zip(LEVELS, INSTANCES))  # type: Dict[int, PermissionLevelItem]

	MAXIMUM_LEVEL = LEVELS[-1]  # type: int
	MINIMUM_LEVEL = LEVELS[0]  # type: int
	MCDR_CONTROL_LEVEL = ADMIN  # type: int
	PHYSICAL_SERVER_CONTROL_LEVEL = OWNER  # type: int
	CONSOLE_LEVEL = MAXIMUM_LEVEL  # type: int
	PLUGIN_LEVEL = MAXIMUM_LEVEL  # type: int

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
