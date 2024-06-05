import collections
import dataclasses
from enum import Enum
from typing import Optional, Dict, List, Union


PermissionParam = Union[str, int]


@dataclasses.dataclass(frozen=True)
class PermissionLevelItem:
	name: str
	level: int

	def __str__(self):
		return '{} ({})'.format(self.level, self.name)

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

	GUEST: int = __Storage.GUEST_.value.level
	USER: int = __Storage.USER_.value.level
	HELPER: int = __Storage.HELPER_.value.level
	ADMIN: int = __Storage.ADMIN_.value.level
	OWNER: int = __Storage.OWNER_.value.level

	INSTANCES: List[PermissionLevelItem] = [item.value for item in __Storage]
	LEVELS: List[int] = [inst.level for inst in INSTANCES]
	NAMES: List[str] = [inst.name for inst in INSTANCES]
	__NAME_DICT: Dict[str, PermissionLevelItem] = collections.OrderedDict(zip(NAMES, INSTANCES))
	__LEVEL_DICT: Dict[int, PermissionLevelItem] = collections.OrderedDict(zip(LEVELS, INSTANCES))

	MAXIMUM_LEVEL: int = LEVELS[-1]
	MINIMUM_LEVEL: int = LEVELS[0]
	MCDR_CONTROL_LEVEL: int = ADMIN
	PHYSICAL_SERVER_CONTROL_LEVEL: int = OWNER
	CONSOLE_LEVEL: int = MAXIMUM_LEVEL
	PLUGIN_LEVEL: int = MAXIMUM_LEVEL

	@classmethod
	def __check_range(cls, level: int):
		if cls.MINIMUM_LEVEL <= level <= cls.MAXIMUM_LEVEL:
			pass
		else:
			raise ValueError('Value {} out of range [{}, {}]'.format(level, cls.MINIMUM_LEVEL, cls.MAXIMUM_LEVEL))

	@classmethod
	def from_value(cls, value: PermissionParam) -> PermissionLevelItem:
		"""
		Convert any type of permission level into int value. Examples:
			'guest'	-> 0
			'admin'	-> 3
			'1'		-> 1
			2		-> 2
		If the argument is invalid return None

		:param value: a permission related object
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
	def get_level(cls, value: PermissionParam) -> Optional[PermissionLevelItem]:
		"""
		Fail-proof version of from_value
		"""
		try:
			return cls.from_value(value)
		except (TypeError, ValueError):
			return None
