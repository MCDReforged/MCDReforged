import dataclasses
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Generic, Union

from typing_extensions import override, Self, final

from mcdreforged.minecraft.rtext._registry import RRegistry, NamedObject
from mcdreforged.minecraft.rtext.schema import RTextJsonFormat
from mcdreforged.utils import class_utils


class __RClickActionMeta(RRegistry['RAction']):
	pass


_RCE = TypeVar('_RCE', bound='RClickEvent')


class RClickAction(NamedObject, ABC, Generic[_RCE], metaclass=__RClickActionMeta):
	"""
	Minecraft click event actions
	"""

	suggest_command: 'RClickAction[RClickSuggestCommand]'
	"""Fill the chat bar with given text"""

	run_command: 'RClickAction[RClickRunCommand]'
	"""
	Run the given text as command

	(Minecraft <1.19.1) If the given text doesn't start with ``"/"``, the given text will be considered as a chat message and sent to the server,
	so it can be used to automatically execute MCDR command after the player click the decorated text

	.. attention:: 

		In vanilla Minecraft >=1.19.1, only strings starting with ``"/"``, i.e. command strings, can be used as the text value of :attr:`run_command` action

		For other strings that don't start with ``"/"``, the client will reject to send the chat message

		See `Issue #203 <https://github.com/MCDReforged/MCDReforged/issues/203>`__
	"""

	open_url: 'RClickAction[RClickOpenUrl]'
	"""Open given url"""

	open_file: 'RClickAction[RClickOpenFile]'
	"""
	Open file from given path

	.. note:: 

		Actually vanilla Minecraft doesn't allow texts sent by command contain :attr:`open_file` actions,
		so don't be surprised if this :attr:`open_file` doesn't work
	"""

	copy_to_clipboard: 'RClickAction[RClickCopyToClipboard]'
	"""
	Copy given text to clipboard

	.. note:: Available in Minecraft 1.15+
	"""

	change_page: 'RClickAction[RClickChangePage]'
	"""
	Change to the specified page of the current book 

	.. note:: 

		Only work in written books
	"""

	show_dialog: 'RClickAction[RClickShowDialog]'
	"""
	Open specified dialog

	.. note:: Available in Minecraft 1.21.6+
	"""

	custom: 'RClickAction[RClickCustom]'
	"""
	Send a custom event to the server, which has no effect in vanilla servers

	.. note:: Available in Minecraft 1.21.6+
	"""

	@property
	@abstractmethod
	def event_class(self) -> Type[_RCE]:
		raise NotImplementedError()


RAction = RClickAction  # The historical alias


class _RClickActionImpl(RClickAction):
	def __init__(self, name: str, event_class: Type['RClickEvent']):
		self.__name = name
		self.__event_class = event_class

	@property
	@override
	def name(self) -> str:
		return self.__name

	@property
	@override
	def event_class(self) -> Type['RClickEvent']:
		return self.__event_class

	def __repr__(self) -> str:
		return class_utils.represent(self, {'action': self.name, 'class': self.__event_class})


@dataclasses.dataclass(frozen=True)
class RClickEvent(ABC):
	@property
	@abstractmethod
	def action(self) -> RClickAction:
		raise NotImplementedError()

	@final
	def to_json_object(self, json_format: RTextJsonFormat) -> dict:
		data = self._to_json_object(json_format)
		data['action'] = self.action.name
		return data

	@abstractmethod
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		raise NotImplementedError()

	@classmethod
	@final
	def from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Optional['RClickEvent']:
		action: str = class_utils.check_type(click_event['action'], str)
		for rca in RClickAction:
			if rca.name == action:
				event_class: RClickEvent = rca.event_class
				return event_class._from_json_object(click_event, json_format)
		return None

	@classmethod
	@abstractmethod
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		raise NotImplementedError()


_T = TypeVar('_T')


class _RClickEventSingleValue(RClickEvent, ABC, Generic[_T]):
	@override
	@final
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		return {self._get_json_key(json_format): self.get_json_value(json_format)}

	@classmethod
	@override
	@final
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		return cls.from_json_value(click_event[cls._get_json_key(json_format)])

	@classmethod
	@abstractmethod
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		raise NotImplementedError()

	@abstractmethod
	def get_json_value(self, json_format: RTextJsonFormat) -> _T:
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def from_json_value(cls, v: _T) -> Self:
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class RClickSuggestCommand(_RClickEventSingleValue[str]):
	command: str

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.suggest_command

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'command' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> str:
		return self.command

	@classmethod
	@override
	def from_json_value(cls, s: str) -> Self:
		return cls(command=class_utils.check_type(s, str))


@dataclasses.dataclass(frozen=True)
class RClickRunCommand(_RClickEventSingleValue[str]):
	command: str

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.run_command

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'command' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> str:
		return self.command

	@classmethod
	@override
	def from_json_value(cls, s: str) -> Self:
		return cls(command=class_utils.check_type(s, str))


@dataclasses.dataclass(frozen=True)
class RClickOpenUrl(_RClickEventSingleValue[str]):
	url: str

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.open_url

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'url' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> str:
		return self.url

	@classmethod
	@override
	def from_json_value(cls, s: str) -> Self:
		return cls(url=class_utils.check_type(s, str))


@dataclasses.dataclass(frozen=True)
class RClickOpenFile(_RClickEventSingleValue[str]):
	path: str

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.open_file

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'path' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> str:
		return self.path

	@classmethod
	@override
	def from_json_value(cls, s: str) -> Self:
		return cls(path=class_utils.check_type(s, str))


@dataclasses.dataclass(frozen=True)
class RClickCopyToClipboard(_RClickEventSingleValue[str]):
	value: str

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.copy_to_clipboard

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> str:
		return self.value

	@classmethod
	@override
	def from_json_value(cls, s: str) -> Self:
		return cls(value=class_utils.check_type(s, str))


@dataclasses.dataclass(frozen=True)
class RClickShowDialog(_RClickEventSingleValue[Union[str, dict]]):
	dialog: Union[str, dict]
	"""
	A dialog identifier, e.g. "minecraft:server_links",
	or a full dialog description NBT tag
	"""

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.show_dialog

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'dialog' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> Union[str, dict]:
		return self.dialog

	@classmethod
	@override
	def from_json_value(cls, v: Union[str, dict]) -> Self:
		return cls(dialog=class_utils.check_type(v, (str, dict)))


@dataclasses.dataclass(frozen=True)
class RClickChangePage(_RClickEventSingleValue[Union[int, str]]):
	page: int

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.change_page

	@classmethod
	@override
	def _get_json_key(cls, json_format: RTextJsonFormat) -> str:
		return 'page' if json_format == RTextJsonFormat.V_1_21_5 else 'value'

	@override
	def get_json_value(self, json_format: RTextJsonFormat) -> Union[int, str]:
		return self.page if json_format == RTextJsonFormat.V_1_21_5 else str(self.page)

	@classmethod
	@override
	def from_json_value(cls, v: Union[int, str]) -> Self:
		return cls(page=int(v))


@dataclasses.dataclass(frozen=True)
class RClickCustom(RClickEvent):
	id: str
	payload: Optional[Union[str, dict]] = None

	@property
	@override
	def action(self) -> RClickAction:
		return RClickAction.custom

	@override
	def _to_json_object(self, json_format: RTextJsonFormat) -> dict:
		# introduced in mc1.21.6, so no need for handling RTextJsonFormat < V_1_21_5
		return {
			'id': self.id,
			**({'payload': self.payload} if self.payload is not None else {}),
		}

	@classmethod
	@override
	def _from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Self:
		# introduced in mc1.21.6, so no need for handling RTextJsonFormat < V_1_21_5
		return cls(
			id=class_utils.check_type(click_event['id'], str),
			payload=class_utils.check_type(click_event.get('payload'), (str, dict, None)),
		)


def __register_click_events():
	def register(name: str, event_class: Type['RClickEvent']):
		RClickAction.register_item(name, _RClickActionImpl(name, event_class))

	register('suggest_command', RClickSuggestCommand)
	register('run_command', RClickRunCommand)
	register('open_url', RClickOpenUrl)
	register('open_file', RClickOpenFile)
	register('copy_to_clipboard', RClickCopyToClipboard)


__register_click_events()
