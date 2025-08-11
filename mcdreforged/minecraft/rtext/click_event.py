import dataclasses
import json
from abc import ABC, abstractmethod
from typing import Optional, Type, TypeVar, Generic, Union, ClassVar

from typing_extensions import override, Self, final

from mcdreforged.minecraft.rtext._registry import RRegistry, NamedObject
from mcdreforged.minecraft.rtext.schema import RTextJsonFormat
from mcdreforged.utils import class_utils


class __RClickActionMeta(RRegistry['RAction']):
	pass


_RCE = TypeVar('_RCE', bound='RClickEvent')


class RClickAction(NamedObject, ABC, Generic[_RCE], metaclass=__RClickActionMeta):
	"""
	Minecraft text click event actions

	.. versionadded:: v2.15.0
	.. note:: For versions before v2.15.0, use :attr:`RAction` instead. You can stick to :attr:`RAction` for maximum compatibility
	"""

	suggest_command: ClassVar['RClickAction[RClickSuggestCommand]']
	"""Fill the chat bar with given text"""

	run_command: ClassVar['RClickAction[RClickRunCommand]']
	"""
	Run the given text as command

	(Minecraft <1.19.1) If the given text doesn't start with ``"/"``, the given text will be considered as a chat message and sent to the server,
	so it can be used to automatically execute MCDR command after the player click the decorated text

	.. attention:: 

		In vanilla Minecraft >=1.19.1, only strings starting with ``"/"``, i.e. command strings, can be used as the text value of :attr:`run_command` action

		For other strings that don't start with ``"/"``, the client will reject to send the chat message

		See `Issue #203 <https://github.com/MCDReforged/MCDReforged/issues/203>`__
	"""

	open_url: ClassVar['RClickAction[RClickOpenUrl]']
	"""Open given url"""

	open_file: ClassVar['RClickAction[RClickOpenFile]']
	"""
	Open file from given path

	.. note:: 

		Actually vanilla Minecraft doesn't allow texts sent by command contain :attr:`open_file` actions,
		so don't be surprised if this :attr:`open_file` doesn't work
	"""

	copy_to_clipboard: ClassVar['RClickAction[RClickCopyToClipboard]']
	"""
	Copy given text to clipboard

	.. note:: Available in Minecraft 1.15+
	"""

	change_page: ClassVar['RClickAction[RClickChangePage]']
	"""
	Change to the specified page of the current book 

	.. note:: Only work in written books
	"""

	show_dialog: ClassVar['RClickAction[RClickShowDialog]']
	"""
	Open specified dialog

	.. note:: Available in Minecraft 1.21.6+
	.. versionadded:: v2.15.0
	"""

	custom: ClassVar['RClickAction[RClickCustom]']
	"""
	Send a custom event to the server, which has no effect in vanilla servers

	.. note:: Available in Minecraft 1.21.6+
	.. versionadded:: v2.15.0
	"""

	@property
	@abstractmethod
	def event_class(self) -> Type[_RCE]:
		raise NotImplementedError()


# The historical alias
RAction = RClickAction
"""
Alias of :class:`RClickAction`

.. versionadded:: v1.0.0
"""


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
	"""
	An abstract base class of Minecraft click event component

	.. versionadded:: v2.15.0
	"""

	@property
	@abstractmethod
	def action(self) -> RClickAction:
		"""
		Return the click action type of this component
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
	def from_json_object(cls, click_event: dict, json_format: RTextJsonFormat) -> Optional['RClickEvent']:
		"""
		Deserialize a json dict to a click event component

		:param click_event: The json dict to deserialize from
		:param json_format: The json format of the provided data
		"""
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


_JsonValueType = TypeVar('_JsonValueType')


class RClickEventSingleValue(RClickEvent, ABC, Generic[_JsonValueType]):
	"""
	An abstract base class for those click event components that contain only 1 value

	.. seealso: :meth:`RTextBase.set_click_event(action, value) <mcdreforged.minecraft.rtext.text.RTextBase.set_click_event>`
	.. versionadded:: v2.15.0
	"""

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
	def get_json_value(self, json_format: RTextJsonFormat) -> _JsonValueType:
		raise NotImplementedError()

	@classmethod
	@abstractmethod
	def from_json_value(cls, v: _JsonValueType) -> Self:
		raise NotImplementedError()


@dataclasses.dataclass(frozen=True)
class RClickSuggestCommand(RClickEventSingleValue[str]):
	"""
	The click event component for :attr:`RClickAction.suggest_command` action

	.. versionadded:: v2.15.0
	"""

	command: str
	"""The command to suggest"""

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
class RClickRunCommand(RClickEventSingleValue[str]):
	"""
	The click event component for :attr:`RClickAction.run_command` action

	.. versionadded:: v2.15.0
	"""

	command: str
	"""The command to run"""

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
class RClickOpenUrl(RClickEventSingleValue[str]):
	"""
	The click event component for :attr:`RClickAction.open_url` action

	.. versionadded:: v2.15.0
	"""

	url: str
	"""The url to open"""

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
class RClickOpenFile(RClickEventSingleValue[str]):
	"""
	The click event component for :attr:`RClickAction.open_file` action

	.. versionadded:: v2.15.0
	"""

	path: str
	"""The file path to open"""

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
class RClickCopyToClipboard(RClickEventSingleValue[str]):
	"""
	The click event component for :attr:`RClickAction.copy_to_clipboard` action

	.. versionadded:: v2.15.0
	"""

	value: str
	"""The content to copy to clipboard"""

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
class RClickShowDialog(RClickEventSingleValue[Union[str, dict]]):
	"""
	The click event component for :attr:`RClickAction.show_dialog` action

	.. note:: Available in Minecraft 1.21.6+
	.. versionadded:: v2.15.0
	"""

	dialog: Union[str, dict]
	"""
	The data of the dialog. It can be either:
	
	1. A dialog identifier, e.g., ``minecraft:server_links``
	2. A full dialog description NBT tag
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
		if json_format == RTextJsonFormat.V_1_7:
			# This was introduced in mc1.21.5 and RTextJsonFormat.V_1_7 does not support this
			# just return something safe for the server (in case it only expects str for the `value` field)
			return self.dialog if isinstance(self.dialog, str) else json.dumps(self.dialog, ensure_ascii=False)
		else:
			return self.dialog if isinstance(self.dialog, str) else self.dialog.copy()  # XXX: deepcopy?

	@classmethod
	@override
	def from_json_value(cls, v: Union[str, dict]) -> Self:
		return cls(dialog=class_utils.check_type(v, (str, dict)))


# The json value type is
#    str, in RTextJsonFormat.V_1_7
#    int, in RTextJsonFormat.V_1_21_5
# Just use `Union[int, str]` here to make it simple
@dataclasses.dataclass(frozen=True)
class RClickChangePage(RClickEventSingleValue[Union[int, str]]):
	"""
	The click event component for :attr:`RClickAction.change_page` action

	.. versionadded:: v2.15.0
	"""

	page: int
	"""The page number to change to"""

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
	"""
	The click event component for :attr:`RClickAction.custom` action

	.. note:: Available in Minecraft 1.21.6+
	.. versionadded:: v2.15.0
	"""

	id: str
	"""The identifier"""

	payload: Optional[Union[str, dict]] = None
	"""(Optional) The payload"""

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
		# noinspection PyProtectedMember
		RClickAction._register_item(name, _RClickActionImpl(name, event_class))

	register('suggest_command', RClickSuggestCommand)
	register('run_command', RClickRunCommand)
	register('open_url', RClickOpenUrl)
	register('open_file', RClickOpenFile)
	register('copy_to_clipboard', RClickCopyToClipboard)
	register('change_page', RClickChangePage)
	register('show_dialog', RClickShowDialog)
	register('custom', RClickCustom)

	# noinspection PyProtectedMember
	RClickAction._ensure_registration_done()


__register_click_events()
