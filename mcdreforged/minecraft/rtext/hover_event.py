import dataclasses
import json
from abc import ABC, abstractmethod
from typing import Optional, TYPE_CHECKING, Type, Dict, Any, Union, TypeVar, Generic, ClassVar
from uuid import UUID

from typing_extensions import override, Self, final

from mcdreforged.minecraft.rtext._registry import RRegistry, NamedObject
from mcdreforged.minecraft.rtext.schema import RTextJsonFormat
from mcdreforged.utils import class_utils

if TYPE_CHECKING:
	from mcdreforged.minecraft.rtext.text import RTextBase


class __RHoverMeta(RRegistry['RHoverAction']):
	pass


_RHE = TypeVar('_RHE', bound='RHoverEvent')


class RHoverAction(NamedObject, ABC, Generic[_RHE], metaclass=__RHoverMeta):
	"""
	Minecraft text hover event actions

	.. versionadded:: v2.15.0
	"""

	show_text: ClassVar['RHoverAction[RHoverText]']
	"""Show hover text"""

	show_entity: ClassVar['RHoverAction[RHoverEntity]']
	"""Show entity information"""

	show_item: ClassVar['RHoverAction[RHoverItem]']
	"""Show item information"""

	@property
	@abstractmethod
	def event_class(self) -> Type[_RHE]:
		raise NotImplementedError()


class _RHoverActionImpl(RHoverAction):
	def __init__(self, name: str, event_class: Type['RHoverEvent']):
		self.__name = name
		self.__event_class = event_class

	@property
	@override
	def name(self) -> str:
		return self.__name

	@property
	@override
	def event_class(self) -> Type['RHoverEvent']:
		return self.__event_class

	def __repr__(self) -> str:
		return class_utils.represent(self, {'action': self.name, 'class': self.__event_class})


@dataclasses.dataclass(frozen=True)
class RHoverEvent(ABC):
	"""
	An abstract base class of Minecraft hover event component

	.. versionadded:: v2.15.0
	"""

	@property
	@abstractmethod
	def action(self) -> RHoverAction:
		"""
		Return the hover action type of this component
		"""
		raise NotImplementedError()

	@final
	def to_json_object(self, json_format: RTextJsonFormat) -> dict:
		"""
		Serialize itself into a json dict

		:param json_format: The target json format
		"""
		data = self._to_json_object(json_format)
		data.pop('action', None)
		return {'action': self.action.name, **data}

	@abstractmethod
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		raise NotImplementedError()

	@classmethod
	@final
	def from_json_object(cls, hover_event: dict, json_format: RTextJsonFormat) -> Optional['RHoverEvent']:
		"""
		Deserialize a json dict to a hover event component

		:param hover_event: The json dict to deserialize from
		:param json_format: The json format of the provided data
		"""
		action: str = class_utils.check_type(hover_event['action'], str)
		for rha in RHoverAction:
			if rha.name == action:
				event_class: RHoverEvent = rha.event_class
				return event_class._from_json_object(hover_event, json_format)
		return None

	@classmethod
	@abstractmethod
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		raise NotImplementedError()


_K = TypeVar('_K')
_V = TypeVar('_V')


def _get_by_any_key(dt: Dict[_K, _V], *keys: _K) -> _V:
	for key in keys:
		if key in dt:
			return dt[key]
	raise KeyError(keys)


@dataclasses.dataclass(frozen=True)
class RHoverText(RHoverEvent):
	"""
	The hover event component for :attr:`RHoverAction.show_text` action

	.. versionadded:: v2.15.0
	"""

	text: 'RTextBase'
	"""The text to be displayed"""

	@property
	@override
	def action(self) -> RHoverAction:
		return RHoverAction.show_text

	@override
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		text_obj = self.text.to_json_object(json_format=json_format)
		if json_format == RTextJsonFormat.V_1_7:
			return {'value': text_obj}
		elif json_format == RTextJsonFormat.V_1_21_5:
			return {'value': text_obj}
		else:
			raise ValueError(json_format)

	@classmethod
	@override
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		if json_format == RTextJsonFormat.V_1_7:
			text_obj = _get_by_any_key(click_event, 'value', 'contents')
		elif json_format == RTextJsonFormat.V_1_21_5:
			text_obj = click_event['value']
		else:
			raise ValueError(json_format)
		from mcdreforged.minecraft.rtext.text import RTextBase
		return cls(text=RTextBase.from_json_object(text_obj))


@dataclasses.dataclass(frozen=True)
class RHoverEntity(RHoverEvent):
	"""
	The hover event component for :attr:`RHoverAction.show_entity` action

	.. versionadded:: v2.15.0
	"""

	id: str
	"""
	The entity type identifier, e.g. ``minecraft:creeper``
	"""

	uuid: UUID
	"""
	The UUID of the entity
	"""

	name: Optional[Union[str, 'RTextBase']] = None
	"""
	(Optional) The custom name of the entity
	"""

	@property
	@override
	def action(self) -> RHoverAction:
		return RHoverAction.show_entity

	@override
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		from mcdreforged.minecraft.rtext.text import RTextBase
		if isinstance(self.name, str):
			name_value = self.name
		elif isinstance(self.name, RTextBase):
			name_value = self.name.to_json_object(json_format=json_format)
		else:
			name_value = None

		if json_format == RTextJsonFormat.V_1_7:
			return {
				'value': json.dumps({
					'type': self.id,
					'id': str(self.uuid),
					**({'name': json.dumps(name_value, ensure_ascii=False)} if name_value is not None else {}),
				}, ensure_ascii=False)
			}
		elif json_format == RTextJsonFormat.V_1_21_5:
			return {
				'id': self.id,
				'uuid': str(self.uuid),
				**({'name': name_value} if name_value is not None else {}),
			}
		else:
			raise ValueError(json_format)

	@classmethod
	@override
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		from mcdreforged.minecraft.rtext.text import RTextBase

		def deserialize_name(value: Any) -> Optional[Union[str, RTextBase]]:
			if value is None or isinstance(value, str):
				return value
			else:
				return RTextBase.from_json_object(value)

		def deserialize_uuid(value: Any) -> UUID:
			if isinstance(value, str):
				return UUID(value)
			elif isinstance(value, list):
				if len(value) != 4:
					raise ValueError('list-like UUID should have exactly 4 elements, got {}'.format(len(value)))
				return UUID(int=(int(value[0]) << 96) | (int(value[1]) << 64) | (int(value[2]) << 32) | int(value[3]))
			else:
				raise TypeError(type(value))

		if json_format == RTextJsonFormat.V_1_7:
			if 'contents' in click_event:
				data = click_event['contents']
			else:
				data = json.loads(click_event['value'])
				if 'name' in data:
					data['name'] = json.loads(data['name'])
			return cls(
				id=class_utils.check_type(data['type'], str),
				uuid=deserialize_uuid(data['id']),
				name=deserialize_name(data.get('name')),
			)
		elif json_format == RTextJsonFormat.V_1_21_5:
			return cls(
				id=class_utils.check_type(click_event['id'], str),
				uuid=deserialize_uuid(click_event['uuid']),
				name=deserialize_name(click_event.get('name')),
			)
		else:
			raise ValueError(json_format)


@dataclasses.dataclass(frozen=True)
class RHoverItem(RHoverEvent):
	"""
	The hover event component for :attr:`RHoverAction.show_item` action

	.. versionadded:: v2.15.0
	"""

	id: str
	"""
	The item type identifier, e.g. ``minecraft:stone``
	"""

	count: Optional[int] = None
	"""
	(Optional) Item count. Although it's optional, it's still suggested provide a value (e.g. 1)
	"""

	components: Optional[dict] = None
	"""
	(Optional) Extra NBT tag / item components information of the item stack
	"""

	@property
	@override
	def action(self) -> RHoverAction:
		return RHoverAction.show_item

	@override
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		if json_format == RTextJsonFormat.V_1_7:
			return {
				'value': json.dumps({
					'id': self.id,
					**({'Count': self.count} if self.count is not None else {}),
					**({'tag': self.components} if self.components is not None else {}),
				}, ensure_ascii=False)
			}
		elif json_format == RTextJsonFormat.V_1_21_5:
			return {
				'id': self.id,
				**({'count': self.count} if self.count is not None else {}),
				**({'components': self.components} if self.components is not None else {}),
			}
		else:
			raise ValueError(json_format)

	@classmethod
	@override
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		if json_format == RTextJsonFormat.V_1_7:
			if 'contents' in click_event:
				data = click_event['contents']
			else:
				data = json.loads(click_event['value'])
			return cls(
				id=class_utils.check_type(data['id'], str),
				count=class_utils.check_type(data.get('Count'), (int, None)),
				components=class_utils.check_type(data.get('tag'), (dict, None)),
			)
		elif json_format == RTextJsonFormat.V_1_21_5:
			return cls(
				id=class_utils.check_type(click_event['id'], str),
				count=class_utils.check_type(click_event.get('count'), (int, None)),
				components=class_utils.check_type(click_event.get('components'), (dict, None)),
			)
		else:
			raise ValueError(json_format)


def __register_hover_events():
	def register(name: str, event_class: Type[RHoverEvent]):
		# noinspection PyProtectedMember
		RHoverAction._register_item(name, _RHoverActionImpl(name, event_class))

	register('show_text', RHoverText)
	register('show_entity', RHoverEntity)
	register('show_item', RHoverItem)

	# noinspection PyProtectedMember
	RHoverAction._ensure_registration_done()


__register_hover_events()
