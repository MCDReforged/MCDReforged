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


def serialize(obj: Any) -> Union[None, int, float, str, list, dict]:
	"""
	A utility function to serialize any object into a json-like python object.
	Here, being json-like means that the return value can be passed to e.g. :func:`json.dumps` directly

	Serialization rules:

	*   Immutable object, including :data:`None`, :class:`int`, :class:`float`, :class:`str` and :class:`bool`, will be directly returned
	*   :class:`list` and :class:`tuple` will be serialized into a :class:`list` will all the items serialized
	*   :class:`dict` will be converted into a :class:`dict` will all the keys and values serialized
	*   Normal object will be converted to a :class:`dict` with all of its public fields.
		The keys are the name of the fields and the values are the serialized field values

	:param obj: The object to be serialized
	:return: The serialized result
	"""
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
	"""
	A utility function to deserialize a json-like object into an object in given class

	If the target class contains nested items / fields, corresponding detailed type annotations are required.
	The items / fields will be deserialized recursively

	Supported target classes:

	*   Immutable object: :data:`None`, :class:`int`, :class:`float`, :class:`str` and :class:`bool`

		* The class of the input data should equal to target class. No implicit type conversion will happen
		* As an exception, :class:`float` also accepts an :class:`int` as the input data

	*   Standard container: :class:`list`, :class:`dict`. Type of its content should be type annotated

		* :class:`typing.List`, :class:`list`: Target class needs to be e.g. ``List[int]`` or ``list[int]`` (python 3.9+)
		* :class:`typing.Dict`, :class:`dict`: Target class needs to be e.g. ``Dict[str, bool]`` or ``dict[str, bool]`` (python 3.9+)

	*   Types in the :external:doc:`typing <library/typing>` module:

		*   :data:`typing.Union`: Iterate through its available candidate classes, and return the first successful deserialization result
		*   :data:`typing.Optional`: Actually it will be converted to a :data:`typing.Union` automatically
		*   :data:`typing.Any`: The input data will be directed returned as the result
		*   :data:`typing.Literal`: The input data needs to be in parameter the of :data:`~typing.Literal`, then the input data will be returned as the result

	*   Normal class: The class should have its fields type annotated. It's constructor should accept 0 input parameter.
		Example class::

			class MyClass:
				some_str: str
				a_list: List[int]

		The input data needs to be a dict. Keys and values in the dict correspond to the field names and serialized field values. Example dict::

			{'some_str': 'foo', 'a_list': [1, 2, 3]}

		Fields are set via ``__setattr__``, non-public fields will be ignored.

	:param data: The json-like object to be deserialized
	:param cls: The target class of the generated object
	:keyword error_at_missing: A flag indicating if an exception should be risen
		if there are any not-assigned fields when deserializing an object. Default false
	:keyword error_at_redundancy: A flag indicating if an exception should be risen
		if there are any unknown input attributes when deserializing an object. Default false
	:raise TypeError: If input data doesn't match target class, or target class is unsupported
	:raise ValueError: If input data is invalid, including :data:`Literal <typing.Literal>` mismatch
		and those error flag in kwargs taking effect
	:return: An object in class ``cls``

	.. versionadded:: v2.7.0
		Added :data:`typing.Literal` support
	"""
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
	elif _get_origin(cls) == getattr(List[int], '__origin__'):
		if isinstance(data, list):
			element_type = _get_args(cls)[0]
			return list(map(lambda e: deserialize(e, element_type, error_at_missing=error_at_missing, error_at_redundancy=error_at_redundancy), data))
		else:
			mismatch(list)

	# Dict
	elif _get_origin(cls) == getattr(Dict[int, int], '__origin__'):
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
						raise ValueError('Missing field {} for class {} in input object {}'.format(attr_name, cls, data))
					elif hasattr(cls, attr_name):
						result.__setattr__(attr_name, copy.copy(getattr(cls, attr_name)))
			if error_at_redundancy and len(input_key_set) > 0:
				raise ValueError('Unknown input attributes {} for class {} in input object {}'.format(input_key_set, cls, data))
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
		>>> print(data.name, data.values)
		abc [1, 2]

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
	if the value is missing, a :func:`copy.copy` of the default value will be assigned

	::

		>>> class MyArray(Serializable):
		... 	array: List[int] = [0]

		>>> a = MyArray(array=[1])
		>>> print(a.array)
		[1]
		>>> b, c = MyArray.deserialize({}), MyArray.deserialize({})
		>>> print(b.array)
		[0]

		>>> b.array == c.array == MyArray.array
		True
		>>> b.array is not c.array is not MyArray.array
		True

	Enum class will be serialized into its member name::

		>>> class Gender(Enum):
		... 	male = 'man'
		... 	female = 'woman'

		>>> class Person(Serializable):
		... 	name: str = 'zhang_san'
		... 	gender: Gender = Gender.male

		>>> data = Person.get_default()
		>>> data.serialize()
		{'name': 'zhang_san', 'gender': 'male'}
		>>> data.gender = Gender.female
		>>> data.serialize()
		{'name': 'zhang_san', 'gender': 'female'}
		>>> Person.deserialize({'name': 'li_si', 'gender': 'female'}).gender == Gender.female
		True
	"""
	__annotations_cache: dict = None
	__annotations_lock = Lock()
	__none_attr = object()

	def __init__(self, **kwargs):
		"""
		Create a :class:`Serializable` object with given field values

		Unspecified public fields with default value in the type annotation will be set to a copy (:func:`copy.copy`) of the default value

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
		Serialize itself into a dict via function :func:`serialize`
		"""
		return serialize(self)

	@classmethod
	def deserialize(cls: Type[Self], data: dict, **kwargs) -> Self:
		"""
		Deserialize a dict into an object of this class via function :func:`deserialize`

		When there are missing fields, automatically copy the class's default value if possible. See :meth:`__init__` for more details
		"""
		return deserialize(data, cls, **kwargs)

	def update_from(self, data: dict):
		vars(self).update(vars(self.deserialize(data)))

	@classmethod
	def get_default(cls: Type[Self]) -> Self:
		"""
		Create an object of this class with default values

		Actually it's implemented by invoking :meth:`Serializable.deserialize <mcdreforged.utils.serializer.Serializable.deserialize>`
		with an empty dict
		"""
		return cls.deserialize({})

	def on_deserialization(self):
		"""
		Invoked after being deserialized

		Don't use, it's not a public API yet

		:meta private:
		"""
		pass
