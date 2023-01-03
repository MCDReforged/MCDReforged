import copy
import sys
from abc import ABC
from enum import EnumMeta, Enum
from threading import Lock
from typing import Union, TypeVar, List, Dict, Type, get_type_hints, Any

_py38 = sys.version_info >= (3, 8)

if _py38:
	from typing import Literal


T = TypeVar('T')


def _get_type_hints(cls: Type):
	try:
		return get_type_hints(cls)
	except:
		return get_type_hints(cls, globalns={})


def _get_origin(cls: Type):
	return getattr(cls, '__origin__', None)


def _get_args(cls: Type) -> tuple:
	return getattr(cls, '__args__', ())


def serialize(obj) -> Union[None, int, float, str, list, dict]:
	if type(obj) in (type(None), int, float, str, bool):
		return obj
	elif isinstance(obj, list) or isinstance(obj, tuple):
		return list(map(serialize, obj))
	elif isinstance(obj, dict):
		return dict(map(lambda t: (t[0], serialize(t[1])), obj.items()))
	elif isinstance(obj.__class__, EnumMeta):
		return obj.name
	try:
		attr_dict = vars(obj).copy()
		# don't serialize protected fields
		for attr_name in list(attr_dict.keys()):
			if attr_name.startswith('_'):
				attr_dict.pop(attr_name)
	except:
		raise TypeError('Unsupported input type {}'.format(type(obj))) from None
	else:
		return serialize(attr_dict)


_BASIC_CLASSES = (type(None), bool, int, float, str, list, dict)


def deserialize(data: Any, cls: Type[T], *, error_at_missing: bool = False, error_at_redundancy: bool = False) -> T:
	def mismatch(*expected_class: Type):
		if expected_class != (cls,):
			classes = ' or '.join(map(str, expected_class))
			raise TypeError('Mismatched input type: expected class {} (deduced from {}) but found data with class {}'.format(classes, cls, type(data)))
		else:
			raise TypeError('Mismatched input type: expected class {} but found data with class {}'.format(cls, type(data)))

	# in case None instead of NoneType is passed
	if cls is None:
		cls = type(None)

	# if the target class is Any, then simply return the data
	if cls is Any:
		return data

	# Union
	# Unpack Union first since the target class is not confirmed yet
	elif _get_origin(cls) == Union:
		for possible_cls in _get_args(cls):
			try:
				return deserialize(data, possible_cls, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
			except (TypeError, ValueError):
				pass
		raise TypeError('Data in type {} cannot match any candidate of target class {}'.format(type(data), cls))

	# Element (None, int, float, str, list, dict)
	# For list and dict, since it doesn't have any type hint, we choose to simply return the data
	elif cls in _BASIC_CLASSES:
		if type(data) is cls:
			return data
		# int is ok for float
		elif cls is float and isinstance(data, int):
			return float(data)
		else:
			if cls is float:
				mismatch(float, int)
			else:
				mismatch(cls)

	# List
	elif _get_origin(cls) == List[int].__origin__:
		if isinstance(data, list):
			element_type = _get_args(cls)[0]
			return list(map(lambda e: deserialize(e, element_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy), data))
		else:
			mismatch(list)

	# Dict
	elif _get_origin(cls) == Dict[int, int].__origin__:
		if isinstance(data, dict):
			key_type = _get_args(cls)[0]
			val_type = _get_args(cls)[1]
			instance = {}
			for key, value in data.items():
				deserialized_key = deserialize(key, key_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
				deserialized_value = deserialize(value, val_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
				instance[deserialized_key] = deserialized_value
			return instance
		else:
			mismatch(dict)

	# Enum
	elif isinstance(cls, EnumMeta):
		if isinstance(data, str):
			return cls[data]
		else:
			mismatch(str)

	# Literal from python 3.8
	elif _py38 and _get_origin(cls) == Literal:
		literals = _get_args(cls)
		if data in literals:
			return data
		else:
			raise ValueError('Input object {} does''t matches given literal {}'.format(data, cls))

	# Object
	elif cls not in _BASIC_CLASSES and isinstance(cls, type):
		if isinstance(data, dict):
			try:
				result = cls()
			except:
				raise TypeError('Failed to construct instance of class {}'.format(type(cls)))
			input_key_set = set(data.keys())
			for attr_name, attr_type in _get_type_hints(cls).items():
				if not attr_name.startswith('_'):
					if attr_name in data:
						result.__setattr__(attr_name, deserialize(data[attr_name], attr_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy))
						input_key_set.remove(attr_name)
					elif error_at_missing:
						raise ValueError('Missing attribute {} for class {} in input object {}'.format(attr_name, cls, data))
					elif hasattr(cls, attr_name):
						result.__setattr__(attr_name, copy.copy(getattr(cls, attr_name)))
			if error_at_redundancy and len(input_key_set) > 0:
				raise ValueError('Redundancy attributes {} for class {} in input object {}'.format(input_key_set, cls, data))
			if isinstance(result, Serializable):
				result.on_deserialization()
			return result
		else:
			mismatch(dict)

	# Unsupported
	else:
		raise TypeError('Unsupported target class: {}'.format(cls))


Self = TypeVar('Self', bound='Serializable')


class Serializable(ABC):
	"""
	An abstract class for easy serializing / deserializing

	Inherit it and declare the fields of your class with type annotations, that's all you need to do

	Example::

		>>> class MyData(Serializable):
		... 	name: str
		... 	values: List[int]

		>>> data = MyData.deserialize({'name': 'abc', 'values': [1, 2]})
		>>> data.serialize()
		{'name': 'abc', 'values': [1, 2]}

		>>> data = MyData(name='cde')
		>>> data.serialize()
		{'name': 'cde'}

	:class:`Serializable` class nesting is also supported::

		class MyStorage(Serializable):
			id: str
			best: MyData
			data: Dict[str, MyData]

	You can also declare default value when declaring type annotations, then during deserializing,
	if the value is missing, a `copy <https://docs.python.org/3/library/copy.html#copy.copy>`__ of the default value will be assigned

	::

		>>> class MyData(Serializable):
		... 	name: str = 'default'
		... 	values: List[int] = []

		>>> data = MyData(values=[0])
		>>> data.serialize()
		{'name': 'default', 'values': [0]}
		>>> MyData.deserialize({}).serialize()
		{'name': 'default', 'values': []}
		>>> MyData.deserialize({}).values is MyData.deserialize({}).values
		False

	Enum class will be serialized into its member name::

		>>> class Gender(Enum):
		... 	male = 'man'
		... 	female = 'woman'

		>>> class MyData(Serializable):
		... 	name: str = 'zhang_san'
		... 	gender: Gender = Gender.male

		>>> data = MyData.get_default()
		>>> data.serialize()
		{'name': 'zhang_san', 'gender': 'male'}
		>>> data.gender = Gender.female
		>>> data.serialize()
		{'name': 'zhang_san', 'gender': 'female'}
		>>> MyData.deserialize({'name': 'li_si', 'gender': 'female'}).gender == Gender.female
		True
	"""
	__annotations_cache: dict = None
	__annotations_lock = Lock()
	__none_attr = object()

	def __init__(self, **kwargs):
		"""
		Create a :class:`Serializable` object with given field values

		Unspecified field with default value in the type annotation will be set to a copy of the default value

		:param kwargs: A dict storing to-be-set values of its fields.
			It's keys are field names and values are field values
		"""
		cls = self.__class__
		for key in kwargs.keys():
			if key not in self.get_annotations_fields():
				raise KeyError('Unknown key received in __init__ of class {}: {}'.format(cls, key))
		for attr_name, attr_type in _get_type_hints(cls).items():
			if not attr_name.startswith('_'):
				if attr_name in kwargs:
					value = kwargs.get(attr_name)
				elif hasattr(cls, attr_name):
					value = copy.copy(getattr(cls, attr_name))
				else:
					value = cls.__none_attr
				if value is not cls.__none_attr:
					self.__setattr__(attr_name, value)

	@classmethod
	def __get_annotation_dict(cls) -> dict:
		public_fields = {}
		for attr_name, attr_type in _get_type_hints(cls).items():
			if not attr_name.startswith('_'):
				public_fields[attr_name] = attr_type
		return public_fields

	@classmethod
	def get_annotations_fields(cls) -> Dict[str, Type]:
		with cls.__annotations_lock:
			if cls.__annotations_cache is None:
				cls.__annotations_cache = cls.__get_annotation_dict()
		return cls.__annotations_cache

	def serialize(self) -> dict:
		"""
		Serialize itself into a dict
		"""
		return serialize(self)

	@classmethod
	def deserialize(cls: Type[Self], data: dict, **kwargs) -> Self:
		"""
		Deserialize a dict into an object of this class
		"""
		return deserialize(data, cls, **kwargs)

	def update_from(self, data: dict):
		vars(self).update(vars(self.deserialize(data)))

	@classmethod
	def get_default(cls: Type[Self]) -> Self:
		"""
		Create an object of this class with default values

		Actually it invokes :meth:`deserialize` with an empty dict
		"""
		return cls.deserialize({})

	def on_deserialization(self):
		"""
		Invoked after being deserialized

		:meta private:
		"""
		pass
