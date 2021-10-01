import copy
from abc import ABC
from enum import EnumMeta
from threading import Lock
from typing import Union, TypeVar, List, Dict, Type, get_type_hints

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


def deserialize(data, cls: Type[T], *, error_at_missing=False, error_at_redundancy=False) -> T:
	# in case None instead of NoneType is passed
	if cls is None:
		cls = type(None)
	# Union
	# Unpack Union first since the target class is not confirmed yet
	if _get_origin(cls) == Union:
		for possible_cls in _get_args(cls):
			try:
				return deserialize(data, possible_cls, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
			except (TypeError, ValueError):
				pass
		raise TypeError('Data in type {} cannot match any candidate of target class {}'.format(type(data), cls))
	# Element (None, int, float, str, list, dict)
	# For list and dict, since it doesn't have any type hint, we choose to simply return the data
	elif cls in _BASIC_CLASSES and type(data) is cls:
		return data
	# float thing
	elif cls is float and isinstance(data, int):
		return float(data)
	# List
	elif _get_origin(cls) == List[int].__origin__ and isinstance(data, list):
		element_type = _get_args(cls)[0]
		return list(map(lambda e: deserialize(e, element_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy), data))
	# Dict
	elif _get_origin(cls) == Dict[int, int].__origin__ and isinstance(data, dict):
		key_type = _get_args(cls)[0]
		val_type = _get_args(cls)[1]
		instance = {}
		for key, value in data.items():
			deserialized_key = deserialize(key, key_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
			deserialized_value = deserialize(value, val_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy)
			instance[deserialized_key] = deserialized_value
		return instance
	# Enum
	elif isinstance(cls, EnumMeta) and isinstance(data, str):
		return cls[data]
	# Object
	elif cls not in _BASIC_CLASSES and isinstance(cls, type) and isinstance(data, dict):
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
		raise TypeError('Unsupported input type: expected class {} but found data with class {}'.format(cls, type(data)))


class Serializable(ABC):
	__annotations_cache: dict = None
	__annotations_lock = Lock()

	def __init__(self, **kwargs):
		for key in kwargs.keys():
			if key not in self.get_annotations_fields():
				raise KeyError('Unknown key received in __init__ of class {}: {}'.format(self.__class__, key))
		vars(self).update(kwargs)

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
		return serialize(self)

	@classmethod
	def deserialize(cls, data: dict, **kwargs):
		return deserialize(data, cls, **kwargs)

	def update_from(self, data: dict):
		vars(self).update(vars(self.deserialize(data)))

	@classmethod
	def get_default(cls):
		return cls.deserialize({})

	def on_deserialization(self):
		"""
		Invoked after being deserialized
		"""
		pass
